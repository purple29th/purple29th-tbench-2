/**
 * InternAuth — true internal SSO before page lands
 * This middleware runs at the edge (X2P / AI Web Agents Reverse Proxy) before Next.js rendering.
 * - No `intern_oauth_token` cookie → 307 to `intern-oidc-gateway.internalmeta.com/login` (or .nest.x2p.facebook.net gateway)
 * - Gateway sets cookie `Domain=.internalmeta.com` after successful SSO + device cert validation
 * - Device cert validated via Airlock: hardware-backed cert in Secure Enclave/TPM, serial via ProxygenHTTPHeaders
 * - OD dev URL must be `https://<od>-3000--nest-dev-proxy.internalmeta.com` to avoid cookie domain mismatch loop
 *   (x2p domain *.nest.x2p.facebook.net sets cookie on .internalmeta.com which browser won't send back → loop)
 * - Public routes bypass auth (health check, embed for Unidash, graphql with token forwarding)
 *
 * This is NOT a cookie simulation (previous Vercel middleware.ts used `bellsprout_internal_sso=meta_passed`).
 * This is real OIDC via @nest/intern-auth which calls InternAuth services.
 */
import { createAuthMiddleware } from '@nest/intern-auth';

export default createAuthMiddleware({
  useOIDC: true,
  usePassthroughForOIDC: true,
  publicRoutes: [
    '/api/health',
    '/api/graphql', // token-based, forwarded to InternGraph via thrift-proxy
    '/api/image-proxy',
    '/embed', // outside (authenticated) group — for Unidash iframe embedding (see HOTD embedding guide)
    '/login',
    '/logged-out',
    '/token-login',
  ],
});

export const config = {
  // Exclude static assets, exactly like Nest template
  matcher: ['/((?!_next/static|_next/image|favicon.ico|manifest.json|sw.js|.*\\.(?:png|jpg|jpeg|gif|svg|webp|ico)).*)'],
};
