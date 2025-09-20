import NextAuth, { NextAuthOptions, Session, User as NextAuthUser, Account, Profile } from 'next-auth';
import AzureADProvider from 'next-auth/providers/azure-ad';
import type { JWT } from 'next-auth/jwt';

function getStringProp(obj: unknown, key: string): string | undefined {
  if (!obj || typeof obj !== 'object') return undefined;
  const v = (obj as Record<string, unknown>)[key];
  return typeof v === 'string' ? v : undefined;
}

function ensureSessionUser(session: Session): Session['user'] {
  if (!session.user) {
    // cast via unknown to avoid `any` and to satisfy TS strictness
    (session as unknown as { user: Session['user'] }).user = {} as Session['user'];
  }
  return session.user as Session['user'];
}

// Add a strongly-typed extension for the JWT we persist
type ExtendedJWT = JWT & {
  oid?: string;
  name?: string;
  email?: string;
  provider?: string;
  accessToken?: string;
  refreshToken?: string;
  accessTokenExpires?: number | string;
};

export const authOptions: NextAuthOptions = {
  providers: [
    AzureADProvider({
      clientId: process.env.AZURE_AD_CLIENT_ID as string,
      clientSecret: process.env.AZURE_AD_CLIENT_SECRET as string,
      authorization: { params: { scope: 'openid profile email offline_access' } },
    }),
  ],
  session: { strategy: 'jwt' },
  callbacks: {
    async jwt(params: { token: JWT; user?: NextAuthUser | null; account?: Account | null; profile?: Profile }) {
      const { token, account, profile } = params;
      const t = token as ExtendedJWT;
      if (account && profile) {
        const oid = getStringProp(profile, 'oid');
        const name = getStringProp(profile, 'name');
        const email = getStringProp(profile, 'email') ?? getStringProp(profile, 'upn');
        if (oid) t.oid = oid;
        if (name) t.name = name;
        if (email) t.email = email;
        t.provider = account.provider;
        // Persist access token (and refresh token if present) so client can call API
        if (account.access_token) t.accessToken = account.access_token;
        if (account.refresh_token) t.refreshToken = account.refresh_token;
        // Optionally store expiry
        if (account.expires_at) t.accessTokenExpires = account.expires_at;
      }
      return t;
    },
    async session(params: { session: Session; token: JWT; user?: NextAuthUser | null }) {
      const { session, token } = params;
      const typedUser = ensureSessionUser(session) as NonNullable<Session['user']>;
      const name = getStringProp(token, 'name');
      const email = getStringProp(token, 'email');
      if (name) typedUser.name = name;
      if (email) typedUser.email = email;
      const oid = getStringProp(token, 'oid');
      if (oid) (session as Session & { oid?: string }).oid = oid;

      // Surface access token to the client session object in a stable location
      const t = token as ExtendedJWT;
      const accessToken = t.accessToken;
      if (accessToken) {
        // put on session.accessToken and also session.user.accessToken for convenience
        (session as Session & { accessToken?: string }).accessToken = accessToken;
        (session.user as Session['user'] & { accessToken?: string }).accessToken = accessToken;
      }

      return session;
    }
  },
  events: {}
};

const handler = NextAuth(authOptions);
export { handler as GET, handler as POST };
