# Local preview (without fbsource Nest CLI) — still internal-only design, no Vercel

This repo `purple29th-tbench-2` is a T-Bench task repo, not fbsource. You can't run `nest build --push` here.
But the internal design is fully implemented in `bellsproutcoverage-internal/app/page.tsx` — optimized senior staff dashboard, no Vercel.

To preview locally (still shows INTERNAL badges, no Vercel hosting):

```bash
cd bellsproutcoverage-internal
npm install
npm run dev # localhost:3000
# or
npx next dev -p 3000
```

Data: `public/team_coverage.json` generated via:
```bash
python3 ../tools/team_mapper.py --dry-run --output public/team_coverage.json
# users 25, subdomains 12, top multimedia 55, mobile_android 19, gaps data_science etc.
```

To deploy fully internal (requires fbsource + devserver/OD):
```bash
# On devserver (WWW+FbSource+Configerator OD type)
cd ~/fbsource
buck run fbcode/nest/cli:cli -- new --app bellsproutcoverage --template nextjs
cp -r ~/purple29th-tbench-2/bellsproutcoverage-internal/app fbcode/nest/apps/bellsproutcoverage/
cp ~/purple29th-tbench-2/bellsproutcoverage-internal/nest.json fbcode/nest/apps/bellsproutcoverage/
cp ~/purple29th-tbench-2/bellsproutcoverage-internal/proxy.ts fbcode/nest/apps/bellsproutcoverage/
cd fbcode/nest/apps/bellsproutcoverage
yarn typecheck && yarn lint
nest build --push
# Verify
curl --cert /var/facebook/credentials/$USER/x509/$USER.pem --cacert /var/facebook/rootcanal/ca.pem https://bellsproutcoverage.nest.x2p.facebook.net/api/health
# Open https://bellsproutcoverage.internalmeta.com (opted via configerator D97030136)
```

See `docs/INTERNAL_HOSTING.md` for deep dive on Nest vs Unidash vs WWW, device cert, OIDC gateway cookie domain loop fix, embed route for Unidash, etc.
