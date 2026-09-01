# BellsproutCoverage — Fully Internal Hosting Deep Dive (No Vercel)

> Result of internal wiki search: Vercel @ Meta is **MSL-only (meta.ai, *mango)**, not available for general internal use. Internal tools default to **WWW** or **Nest**.
> Source: https://www.internalfb.com/wiki/Building_web_surfaces_%28websites%2C_landing_pages%2C_blogs%2C_etc.%29_Guide/Product_Development_on_Alt-Stack_Infrastructure/
> Nest infra doc: https://www.internalfb.com/wiki/Nest/Getting_Started_with_Nest/
> Codimango itself is migrating: multimango.com Next.js app → https://codimango.internalmeta.com (Nest)

## 1. Why public .com can't do true Meta SSO

Public Vercel edge:
- No access to corp device cert (hardware-backed Secure Enclave/TPM, checked via Airlock/InternAuth)
- No InternAuth — can't call `ViewerContextInternModule`, `ProxygenHTTPHeaders::getValidatedClientCertSerial()`
- OD bypasses prod MFA wall, prod `internalfb.com` enforces MFA + client cert. iOS Simulator blocked by design (not managed device, no Secure Enclave). Guide: https://www.internalfb.com/wiki/Client_Platform_Engineering/Client_Security/Facebook_ZeroTrust_%28FBZ%29/Accessing_Intern_from_iOS_Simulator/
- Previous attempt with GitHub OAuth clone asking for org password → Google Safe Browsing flagged "Dangerous site" (phishing)

True internal SSO = request blocked at L7 **before** landing, only internal device with valid cert + `intern_oauth_token`/InternAuth session continues. Like `codimango.internalmeta.com/teams`.

## 2. Options for fully internal (ranked)

### Option A: Nest (RECOMMENDED) — Next.js on Meta infra, Vercel-like DX

**What it is:**
- Next.js 16 + React 19 + TypeScript 5.8, Tailwind, StyleX
- Meta's container: fbcode/nest/apps/{app_name} → Podman Docker → vmvm-registry.fbinfra.net/nest/{app} → Tupperware FaaS (X2P) → https://{app}.nest.x2p.facebook.net and https://{hash}--{app}.internalmeta.com
- Build: `<2 min` deploy, per-commit URLs, automatic HTTPS, health checks
- Auth: CAT, OIDC via `@nest/intern-auth`, InternGraph GraphQL, XDB MySQL, OTEL→Scuba logs
- 1200+ apps prod, 5000 drafts, domain discussion for `internalmeta.com` vs `internalnest.com`

**Deployment flow:**
```
Developer Code → nest build (Next.js build standalone) → podman build → tag → vmvm-registry.fbinfra.net/nest/{app} → Tupperware FaaS → AI Web Agents Reverse Proxy (*.ai-web-agents.edge.x2p.facebook.net) → Production URL https://{app}.nest.x2p.facebook.net
 NOT Vercel, NOT AWS/GCP — 100% internal
```

**Prereqs:**
- Company laptop/desktop, svnuser, dev env perms fburl.com/devenvaccess
- VS Code @ Meta, connect to Devserver or OD (type WWW+FbSource+Configerator) — comes with `nest` CLI pre-installed
- Personal oncall: https://www.internalfb.com/oncall/create — Name `{unixname}_oncall`, Rotation Non-Guaranteed, 2 members, Non-critical ON

**Scaffold from scratch (starting at beginning):**
```bash
# on devserver/OD, inside fbsource
cd ~/fbsource
buck run fbcode/nest/cli:cli -- new --app bellsproutcoverage --template nextjs
# or
mkdir -p fbcode/nest/apps/bellsproutcoverage
cd fbcode/nest/apps/bellsproutcoverage
pnpm init; pnpm add next@14.2.5 react@^18 react-dom@^18 @nest/next-core @nest/intern-auth
```

Required files (checklist from Nest wiki):
- `nest.json` — { "oncall": "bellsproutcoverage_oncall", "name": "bellsproutcoverage" }
- `package.json` — has `@nest/next-core` dep
- `next.config.ts` — `import baseConfig from '@nest/next-core/config'; export default { ...baseConfig }`
- `app/api/health/route.ts` — returns `{ status: "healthy" }`
- `proxy.ts` — auth middleware (see below)
- `tunnels.json` — if using XDB
- `.env.production` — prod env

**Auth — true internal SSO before page lands:**

`proxy.ts`:
```ts
import { createAuthMiddleware } from '@nest/intern-auth';

export default createAuthMiddleware({
  useOIDC: true,
  usePassthroughForOIDC: true,
  publicRoutes: [
    "/api/health",
    "/api/graphql", // uses token-based auth
    "/api/image-proxy",
    "/login",
    "/logged-out",
    "/token-login"
  ]
});
export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|manifest.json|sw.js|.*\\.(?:png|jpg|jpeg|gif|svg|webp|ico)).*)"]
};
```

How it works (traced from intern OIDC gateway post):
1. Request to `https://92252-od-3000--nest-dev-proxy.internalmeta.com/...` carries no `intern_oauth_token` → middleware 307 to `intern-oidc-gateway.internalmeta.com/login`
2. Gateway login → sets cookie `intern_oauth_token` with `Domain=.internalmeta.com`
3. Browser retries with cookie → 200, no loop. If using `*.nest.x2p.facebook.net` dev URL, cookie domain mismatch → loops (fix: use `*.internalmeta.com` dev URL: `https://<od>-3000--nest-dev-proxy.internalmeta.com`)
4. Edge checks device cert: hardware-backed cert in Secure Enclave/TPM, validated via `XInternInternAuthDiagnosticsController`, `InternalAccessChecker::genCheckX`. Blocked if not managed device / no valid cert serial.

**Build & push:**
```bash
yarn typecheck && yarn lint && arc lint
nest build                 # local
nest build --push          # builds Docker image + pushes to vmvm-registry + deploys to Tupperware
nest deployment list --app bellsproutcoverage
curl --cert /var/facebook/credentials/$USER/x509/$USER.pem --cacert /var/facebook/rootcanal/ca.pem https://bellsproutcoverage.nest.x2p.facebook.net/api/health
# Prod URLs:
# https://bellsproutcoverage.nest.x2p.facebook.net
# https://{hash}--bellsproutcoverage.internalmeta.com (when opted into internalmeta.com via configerator — D97030136)
```

Intern dataproject creation (if you hit egress):
- DATA_PROJECT ACL needed for FwdProxy. Check https://www.internalfb.com/amp/ACL/DATA_PROJECT:bellsproutcoverage
- If 404 → https://www.internalfb.com/intern/data_project/ → Lookup & Create → Oncall your personal oncall → Create NEW Data Project ACL name = app name

**BellsproutCoverage logic in Nest:**
- Data generation stays local: `tools/team_mapper.py --dry-run` scans `*/task.toml` via tomllib → `team_coverage.json` with `team_users` 25, `subdomain_coverage` (multimedia 53, mobile_android 19), `team_data` with repos per user (purple29th 3, mehag 3, etc.)
- In Nest, put `team_coverage.json` in `public/` or fetch from Manifold/XDB. Or run mapper in Sandcastle as cron → write to XDB shard `xdb.nest_bellsproutcoverage` → query via Drizzle ORM.

See `src/App.tsx` for React version that replicates previous dashboard but for Nest.

### Option B: Unidash Dashboard (Fastest for internal dashboarding)

**Use when:** You want Blank Page dashboard with permissions, not full code ownership.

Steps from wiki:
1. bunnylol `unidash` → https://www.internalfb.com/intern/unidash → "+ Create New Data Asset" → Unidash → Name `BellsproutCoverage` → Permissions (team) → Blank Page → Title "Team Coverage" → Finish
2. Add widgets: toolbar "+ Widget" → Add data source → URL → paste Daiquery URL (if you have query for task.toml data in Hive/Presto) or Scuba/ODS
3. For custom React code (like previous Next.js dashboard), need Nest embed pattern (Hatch):
   - Hatch lets you vibe-create Nest app, but not discoverable from iData. Embed into Unidash:
   - In your Nest app, create `/embed` route **outside** `(authenticated)` group — same content, no CAT auth
   - Add `/embed` to `publicRoutes` in `proxy.ts`
   - Add iframe headers in `next.config.ts`:
     ```js
     async headers() {
       return [{ source: "/embed", headers: [
         { key: "X-Frame-Options", value: "SAMEORIGIN" },
         { key: "Content-Security-Policy", value: "frame-ancestors 'self' *.facebook.com *.internalfb.com *.intern.facebook.com" }
       ]}]
     }
     ```
   - Don't use +Widget → paste Nest URL (fails). Instead: Right-click canvas → Copy some text Widget → Paste as New Widget → Widget Settings → search "iframe" under Other Views → Data source URI → Paste `https://bellsproutcoverage.nest.x2p.facebook.net/embed`
   - Landmine: 405 / No Data Available → CAT minting fails in cross-origin iframe. Fix: Replace `createGraphQLHandler` with custom `/api/graphql` route using `@nest/thrift-proxy` fallback to server-identity auth for read-only Presto (no popups, no expiring tokens) — diffs D93782444, D98157825, D92887910 etc.
4. Save → Publish. Dashboard protected by InternAuth automatically, device cert at edge.

### Option C: WWW (www.internalfb.com) internal route

Legacy path, still supported for internal tools:
- Create `flib/intern/bellsproutcoverage/` or `www/flib/intern/...`
- Controller extends `InternController`, checks `ViewerContextInternModule::getAccountIDInIntern()`, `ProxygenHTTPHeaders::getValidatedClientCertSerial()`, `getValidatedUserPrincipalName()`
- InternAuth status page: https://www.internalfb.com/intern/auth/status for debugging valid headers
- Test via OD: `https://www.{od}.internalfb.com/intern/bellsproutcoverage` (OD bypasses prod MFA wall)
- Physical managed device required for prod `internalfb.com` (hardware-backed cert per https://www.internalfb.com/wiki/Internal_Tools/Intern_Auth/)
- Deploy via WWW push train (slow vs Nest's 2min)

### What to pick for BellsproutCoverage?

- Need: searchable team (25 users), repo mapping (Private repos visible to org members automatically — org search API, not needing per-repo perm), full domain breakdown table working dropdown, real counts not fake 100%, gaps → generate task, Watch Mango validations, dynamic baseline to user's first repo, internal-only SSO before page lands?
- **Nest wins:** You keep Next.js/React 18, Tailwind, same file-based routing as Vercel you liked, but hosted 100% internal with true device-cert SSO. Same `npm run dev` DX, `nest build --push` deploy. Codimango web app itself is migrating to Nest (`codimango.internalmeta.com`), so you align with org.
- **Unidash wins if** you want zero code maintenance + permissions + sharing via URL, but you lose custom searchable UI unless you embed Nest.

## 3. Data pipeline internal

- Generate `team_coverage.json` locally: `python3 tools/team_mapper.py --dry-run` (tomllib scan of `*/task.toml` — totals, subdomain_coverage, domain_coverage, gaps <2 tasks, suggestions)
- For internal: Upload `team_coverage.json` to Manifold `manifold://codimango_metrics/bellsproutcoverage/team_coverage.json` or XDB `xdb.nest_bellsproutcoverage` table `coverage` (columns: subdomain, count)
- Nest app fetches at build time via `fetch()` or at runtime via InternGraph → Presto if you hive-ify tasks.

## 4. Domain parking (no Vercel)

- `bellsproutcoverage.com` bought Namecheap Active Aug 31 2026-2027 Privacy ON, BasicDNS, Parking Page OFF previously, A @ 76.76.21.21, CNAME www cname.vercel-dns.com
- For internal-only: Set Namecheap → Domain List → Parking Page ON, Advanced DNS → delete A/CNAME, keep only TXT SPF. Keep privacy ON. Keep `.com` parked, internal URL is `bellsproutcoverage.internalmeta.com` or `bellsproutcoverage.nest.x2p.facebook.net`
- `.ai` on Porkbun ~$75/yr cheapest, Namecheap ~$85/yr — only if you want external vanity, but not needed for internal

## 5. Minimal Nest app scaffold (from scratch)

```
fbcode/nest/apps/bellsproutcoverage/
├── nest.json
├── package.json (next 14.2.5, @nest/next-core, @nest/intern-auth)
├── next.config.ts
├── proxy.ts
├── app/
│   ├── layout.tsx (InternAuthOIDCProvider)
│   ├── page.tsx (searchable team, domain dropdown — see src/App.tsx)
│   ├── login/page.tsx (OIDC login)
│   ├── (authenticated)/... (gated routes)
│   ├── embed/page.tsx (outside auth group for Unidash iframe embed)
│   └── api/
│       ├── health/route.ts
│       └── graphql/route.ts (custom thrift-proxy fallback, no CAT bridge)
├── public/
│   └── team_coverage.json
└── TARGETS (buck)
```

`TARGETS`:
```
load("@fbcode_macros//build_defs:nest_app.bzl", "nest_app_targets")
nest_app_targets(
    oncall("bellsproutcoverage_oncall"),
)
```

See `src/App.tsx` for drop-in React component.

## 6. Verification

- `nest deployment info --app bellsproutcoverage` → Tupperware logs URL
- `curl --cert ... https://bellsproutcoverage.nest.x2p.facebook.net/api/health` → `{"status":"healthy"}`
- Browser: visit `https://bellsproutcoverage.internalmeta.com` → Intern OIDC Gateway → login → redirect back with `intern_oauth_token` cookie domain `.internalmeta.com` → 200
- Non-managed device / no cert → blocked at InternAuth page (https://www.internalfb.com/intern/auth/status shows missing headers)
- OD: `https://www.{od}.internalfb.com/intern/auth/status` works without MFA wall for testing

## 7. References

- Nest Getting Started: https://www.internalfb.com/wiki/Nest/Getting_Started_with_Nest/
- Nest Infra Deep Dive: https://www.internalfb.com/wiki/Puneet%27s_Understanding_of_Nest/
- Make a NEST App: https://docs.google.com/document/d/16n63d2FiutW94R5wA0ZDys4rTrR1nVAro0odyWWpe3s
- XDO Build Nest Page with AI (three pillars Nest+XDB+Manifold): https://www.internalfb.com/wiki/XDO_Advanced_Development/How_to_Build_a_Nest_Page_with_AI/
- Unidash Create: https://www.internalfb.com/wiki/Unidash-guide/How_to/create-a-new-dashboard/
- HOTD Embedding Hatch into Unidash (embed route, publicRoutes, iframe headers, CAT bridge landmine): https://fb.workplace.com/groups/hack.of.the.day/permalink/31221603950794822/
- Building web surfaces guide (Vercel MSL-only): https://www.internalfb.com/wiki/Building_web_surfaces_%28websites%2C_landing_pages%2C_blogs%2C_etc.%29_Guide/Product_Development_on_Alt-Stack_Infrastructure/
- Codimango arch migrating to Nest: https://www.internalfb.com/wiki/Codimango_design/ + https://docs.google.com/document/d/1_9sMlMvZkn_feuM08yY79rgOz019VQ_i5Hf_4Ttu8ak
- InternAuth / Device cert: https://www.internalfb.com/wiki/Internal_Tools/Intern_Auth/ + Client Platform Eng ZeroTrust: https://www.internalfb.com/wiki/Client_Platform_Engineering/Client_Security/Facebook_ZeroTrust_%28FBZ%29/Accessing_Intern_from_iOS_Simulator/
- D97030136 read domain from configerator for internalmeta.com opt-in
