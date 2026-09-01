# BellsproutCoverage — Internal-Only Rebuild (No Vercel)

> Previous public deployment on `bellsproutcoverage.com` (Vercel) taken down:
> - `vercel alias rm bellsproutcoverage.com/.vercel.app/www` 
> - `vercel domains remove bellsproutcoverage.com`
> - `vercel project remove` → `No projects found`
> - `curl -I https://bellsproutcoverage.com` → `404 DEPLOYMENT_NOT_FOUND`
> - GitHub `bellsproutcoverage/` folder deleted locally (commit 42be483) and never existed on `origin/main` → already 404

This doc is the **from-scratch internal-only** rebuild — no Vercel at all.

## Requirements (from original ask)

- **Team source:** `https://codimango.internalmeta.com/teams?user=purple29th&team=home`
  Prasanna Kumar team, 25 people, 14 reviewers, 291 submitted / 199 reviewed
  Members: `prasannajp 4 submitted 1 accepted, anishh 19/15, aryasa 27/17, mehag 16/15, purple29th 39/3, ...`
- **GitHub org mapping:** `https://github.com/codimango/` via "Find a repository…" search bar showing 10 of 2015 repos. Must show Private repos for org members automatically without extra repo permission. Validated:
  - search `purple29th` → 3 Private `purple29th-tbench-2, purple29th-tbench, purple29th-android-tbench`
  - search `mehag` → 3 `mehag-multimodal-agents Internal Python, swe-bench-pro-mehag Private Shell, mehag-tbench Private Python`
  - Everybody findable, not only 1 user with repos and 24 with 0.
- **Domains:** All actual domains from codebase scan `*/task.toml` via `tomllib`, not incomplete fake list.
  Real counts: `multimedia_and_signal_processing 53`, `mobile_android 19 (largest)`, `unknown 4`, `database_internals 3`, `distributed_systems 2-3`, `scientific_computing 2`, `security_and_privacy 1`, `systems_and_infra 1`, `build_and_ci 1`, `backend_services 1`
  Sub-categories: INFRASTRUCTURE `systems_and_infra, ml_ai_infra, networking, distributed_systems, backend_services, data_infra, build_and_ci`, WEB `web_backend, web_frontend, web_fullstack`, DATA `machine_learning, scientific_computing, data_science, data_analytics, multimedia_and_signal_processing`, PLATFORM `security_and_privacy, caching, state_management, database_internals`
  Counts = tasks covered, not fake 100%
- **UI:** One page, searchable team → repo mapping (Google link to gate), domain breakdown table with working dropdown (All / INFRA / MOBILE / WEB / DATA / PLATFORM), coverage as counts, gaps → `python tools/auto_task_gen.py --name <gap>-task --magic VVTH`, Watch Mango validation loop like `solar-wafer-microcrack-true-area Accepted v2.0` example (Structural 10, Oracle 3/3, Solvability avocado 2/5 not trivial, Quality Review, Contamination, Provenance CLEAN, Dedup Novel 0.63, with Request Changes handling like aniso `sx==sy` not tested, halo-growth skippable)
- **SSO:** Internal-only strictly before page lands — only internal users can logon, blocked first by internal SSO, can only continue if using internal device, automatic not GitHub SSO, like `codimango.internalmeta.com`. Baseline dynamic to current user's first repo (e.g., search `mehag` → `mehag-tbench` not hardcoded `708fe4d`), team not hardcoded to my team when someone else pulls.
- **Domain:** `bellsproutcoverage.com` bought on Namecheap Active Aug 31 2026-2027 Privacy ON, BasicDNS, now parked. `Bellsproutcoverage.ai` idea cheap on Porkbun ~$75/yr. Internal site should NOT use .com, should be `*.internalmeta.com` or `*.intern.facebook.com` for device cert.

## Why Vercel .com can't do true Meta SSO

1. Public internet edge — no access to Meta corp device certificate store
2. No InternAuth — Vercel can't call `InternUser` or check device compliance
3. GitHub OAuth clone asking for org password flagged as phishing → Google Safe Browsing Dangerous site warning (we hit this)
4. Cookie simulation `bellsprout_internal_sso=meta_passed` + `middleware.ts` 307 → only simulates, not real device cert

True Meta SSO requires hosting **behind intern edge**: request blocked at L7 before your code runs, only internal device with valid cert + SSO token can continue.

See `docs/INTERNAL_HOSTING.md` for deep dive.
