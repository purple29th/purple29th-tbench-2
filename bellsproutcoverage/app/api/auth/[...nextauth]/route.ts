import NextAuth from "next-auth";
import GithubProvider from "next-auth/providers/github";

const handler = NextAuth({
  providers: [
    GithubProvider({
      clientId: process.env.GITHUB_ID ?? "",
      clientSecret: process.env.GITHUB_SECRET ?? "",
      authorization: {
        params: { scope: "read:org repo" },
      },
    }),
  ],
  callbacks: {
    async signIn({ account, profile }) {
      // Internal only: check if user is member of codimango org
      // If GITHUB_ID not set (local dev without env), allow for testing
      if (!process.env.GITHUB_ID) {
        return true;
      }
      try {
        const res = await fetch("https://api.github.com/user/memberships/orgs/codimango", {
          headers: {
            Authorization: `Bearer ${account?.access_token}`,
            Accept: "application/vnd.github.v3+json",
          },
        });
        // 200 = member, 404 = not member, 302 = not member
        // For Private orgs, need to check state
        if (res.status === 200) {
          const data = await res.json();
          // state: active means member
          return data.state === "active" || data.state === "pending";
        }
        // Fallback: try list orgs
        const orgsRes = await fetch("https://api.github.com/user/orgs", {
          headers: {
            Authorization: `Bearer ${account?.access_token}`,
          },
        });
        if (orgsRes.ok) {
          const orgs = await orgsRes.json();
          return orgs.some((o: any) => o.login === "codimango");
        }
        return false;
      } catch {
        // If check fails, deny for safety when env is set
        return false;
      }
    },
    async session({ session, token }) {
      // Attach username to session for dynamic team/baseline
      if (token) {
        (session as any).username = token.preferred_username || (session.user as any)?.name || token.name;
      }
      return session;
    },
    async jwt({ token, account, profile }) {
      if (profile) {
        (token as any).preferred_username = (profile as any).login;
      }
      return token;
    },
  },
  pages: {
    signIn: "/login",
  },
});

export { handler as GET, handler as POST };
