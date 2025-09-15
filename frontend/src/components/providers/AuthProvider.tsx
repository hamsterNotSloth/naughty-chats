"use client";
import { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { PublicClientApplication, AccountInfo, InteractionRequiredAuthError, AuthenticationResult } from '@azure/msal-browser';
import { MsalProvider, useMsal } from '@azure/msal-react';

interface UserClaims {
  email?: string;
  preferred_username?: string;
  oid?: string;
  name?: string;
}

interface AppUser {
  id: string;
  email: string;
  username: string;
  gemBalance: number;
  isActive: boolean;
}

interface AuthContextType {
  user: AppUser | null;
  isLoading: boolean;
  login: () => void;
  logout: () => void;
  acquireApiToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// MSAL configuration from env
const tenantName = process.env.NEXT_PUBLIC_B2C_TENANT_NAME; // e.g. yourtenant
const policy = process.env.NEXT_PUBLIC_B2C_USER_FLOW; // e.g. B2C_1_SIGNUPSIGNIN
const authority = process.env.NEXT_PUBLIC_ENTRA_AUTHORITY || (tenantName && policy ? `https://${tenantName}.b2clogin.com/${tenantName}.onmicrosoft.com/${policy}/v2.0` : undefined);
const clientId = process.env.NEXT_PUBLIC_ENTRA_CLIENT_ID as string;
const apiScope = process.env.NEXT_PUBLIC_ENTRA_API_SCOPE as string; // e.g. api://APP_ID/access or .default

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
  const [user, setUser] = useState<AppUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const selectAccount = (list: AccountInfo[]): AccountInfo | null => list.length > 0 ? list[0] : null;

  const acquireApiToken = useCallback(async (): Promise<string | null> => {
    const account = selectAccount(accounts);
    if (!account) return null;
    try {
      const res = await instance.acquireTokenSilent({ scopes: [apiScope], account });
      return res.accessToken;
    } catch (e) {
      if (e instanceof InteractionRequiredAuthError) {
        const res = await instance.acquireTokenPopup({ scopes: [apiScope] });
        return res.accessToken;
      }
      return null;
    }
  }, [accounts, instance]);

  const loadBackendUser = useCallback(async () => {
    const token = await acquireApiToken();
    if (!token) { setIsLoading(false); return; }
    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
    try {
      const resp = await fetch(`${apiBase}/api/me`, { headers: { Authorization: `Bearer ${token}` } });
      if (resp.ok) {
        const data = await resp.json();
        setUser(data);
      }
    } catch {
      /* swallow */
    } finally {
      setIsLoading(false);
    }
  }, [acquireApiToken]);

  useEffect(() => { loadBackendUser(); }, [loadBackendUser]);

  const login = () => {
    instance.loginRedirect({ scopes: [apiScope] });
  };
  const logout = () => {
    instance.logoutRedirect();
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout, acquireApiToken }}>
      {children}
    </AuthContext.Provider>
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