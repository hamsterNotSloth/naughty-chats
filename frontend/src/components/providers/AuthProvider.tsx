"use client";
import { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { PublicClientApplication, AccountInfo, InteractionRequiredAuthError } from '@azure/msal-browser';
import { MsalProvider, useMsal } from '@azure/msal-react';
import { useSession, signIn as nextSignIn, signOut as nextSignOut, getSession } from 'next-auth/react';

export interface UserClaims { email?: string; preferred_username?: string; oid?: string; name?: string; }
export interface AppUser { id: string; email: string; username: string; gemBalance: number; isActive: boolean; }
export interface AuthContextType { user: AppUser | null; isLoading: boolean; login: () => Promise<void>; logout: () => Promise<void>; acquireApiToken: () => Promise<string | null>; }

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// MSAL configuration from env
const tenantName = process.env.NEXT_PUBLIC_B2C_TENANT_NAME;
const policy = process.env.NEXT_PUBLIC_B2C_USER_FLOW;
const explicitAuthority = process.env.NEXT_PUBLIC_ENTRA_AUTHORITY;
const derivedAuthority = (tenantName && policy)
  ? `https://${tenantName}.b2clogin.com/${tenantName}.onmicrosoft.com/${policy}/v2.0`
  : undefined;
const authority = explicitAuthority || derivedAuthority;
const clientId = process.env.NEXT_PUBLIC_ENTRA_CLIENT_ID as string;
const apiScope = process.env.NEXT_PUBLIC_ENTRA_API_SCOPE as string; // e.g. api://APP_ID/User.Impersonation or .default

const msalInstance = new PublicClientApplication({
  auth: {
    clientId,
    authority: authority,
    knownAuthorities: authority ? [authority.split('/v2.0')[0]] : [],
    redirectUri: typeof window !== 'undefined' ? window.location.origin : undefined,
    postLogoutRedirectUri: typeof window !== 'undefined' ? window.location.origin : undefined,
  },
  cache: { cacheLocation: 'localStorage', storeAuthStateInCookie: false }
});

function CoreAuthProvider({ children }: { children: React.ReactNode }) {
  const { instance, accounts } = useMsal();
  const sessionHook = useSession();
  const session = sessionHook?.data;
  const status = sessionHook?.status;
  const [user, setUser] = useState<AppUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const selectAccount = (list: AccountInfo[]): AccountInfo | null => list.length > 0 ? list[0] : null;

  // Primary token acquisition: prefer NextAuth session access token (from provider)
  const acquireApiToken = useCallback(async (): Promise<string | null> => {
    // If NextAuth session has accessToken, return it
    try {
      if (session && (session as unknown as { accessToken?: string }).accessToken) return (session as unknown as { accessToken?: string }).accessToken as string;
      // Fallback: try to read NextAuth session from client (in case hook not hydrated yet)
      const s = await getSession();
      if (s && (s as unknown as { accessToken?: string }).accessToken) return (s as unknown as { accessToken?: string }).accessToken as string;
    } catch (_) { /* ignore */ }

    // Fallback to MSAL flows for environments where we use msal directly
    const account = selectAccount(accounts);
    if (!account) return null;
    try {
      const res = await instance.acquireTokenSilent({ scopes: [apiScope], account });
      return (res as unknown as { accessToken: string }).accessToken;
    } catch (e) {
      if (e instanceof InteractionRequiredAuthError) {
        try {
          const res = await instance.acquireTokenPopup({ scopes: [apiScope] });
          return (res as unknown as { accessToken: string }).accessToken;
        } catch {
          return null; // user did not complete interaction
        }
      }
      return null;
    }
  }, [accounts, instance, session]);

  const loadBackendUser = useCallback(async () => {
    const token = await acquireApiToken();
    if (!token) { setIsLoading(false); return; }
    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
    try {
      const resp = await fetch(`${apiBase}/api/me`, { headers: { Authorization: `Bearer ${token}` } });
      if (resp.ok) {
        const data = await resp.json();
        setUser(data as AppUser);
      }
    } catch { /* ignore */ } finally { setIsLoading(false); }
  }, [acquireApiToken]);

  useEffect(() => { loadBackendUser(); }, [loadBackendUser, session]);

  const login = async () => {
    // Try NextAuth first (opens provider popup/redirect depending on provider settings)
    try {
      await nextSignIn('azure-ad', { callbackUrl: '/' });
      // next-auth will handle redirect; we still attempt to refresh backend user after flow
      await loadBackendUser();
      return;
    } catch (e) {
      // fallback to MSAL popup
    }

    const existing = selectAccount(instance.getAllAccounts());
    if (existing) {
      try {
        await instance.acquireTokenSilent({ scopes: [apiScope], account: existing });
        loadBackendUser();
        return;
      } catch {/* ignore and proceed to popup */}
    }
    try {
      await instance.loginPopup({ scopes: [apiScope] });
      loadBackendUser();
    } catch {
      // Popup blocked or user closed it.
    }
  };

  const logout = async () => {
    try {
      await nextSignOut({ callbackUrl: '/' });
    } catch {
      // fallback to MSAL logout
      instance.logoutPopup().catch(() => instance.logoutRedirect());
    }
  };

  return (
    <AuthContext.Provider value={{ user, isLoading: status === 'loading' || isLoading, login, logout, acquireApiToken }}>{children}</AuthContext.Provider>
  );
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  return (
    <MsalProvider instance={msalInstance}>
      <CoreAuthProvider>{children}</CoreAuthProvider>
    </MsalProvider>
  );
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}