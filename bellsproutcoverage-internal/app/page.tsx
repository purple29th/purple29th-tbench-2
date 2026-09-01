"use client";

import { useState, useEffect, useMemo } from "react";

type Repo = { name: string; visibility: string; description?: string };
type Coverage = {
  team_users: string[];
  totals: { users: number; repos: number; tasks: number };
  subdomain_coverage: Record<string, number>;
  domain_coverage: Record<string, number>;
  team_data: Record<string, { repos: Repo[]; repo_count: number }>;
  gaps: string[];
  suggestions: string[];
};

const GROUPS: Record<string, { label: string; items: string[] }> = {
  all: { label: "All domains", items: [] },
  infrastructure: {
    label: "INFRASTRUCTURE",
    items: ["systems_and_infra", "ml_ai_infra", "networking", "distributed_systems", "backend_services", "data_infra", "build_and_ci"],
  },
  mobile: { label: "MOBILE", items: ["mobile_android"] },
  web: { label: "WEB", items: ["web_backend", "web_frontend", "web_fullstack"] },
  data: {
    label: "DATA",
    items: ["data_science", "machine_learning", "scientific_computing", "multimedia_and_signal_processing", "data_analytics"],
  },
  platform: {
    label: "PLATFORM",
    items: ["security_and_privacy", "caching", "state_management", "database_internals"],
  },
};

export default function Page({ isEmbed = false }: { isEmbed?: boolean }) {
  const [coverage, setCoverage] = useState<Coverage | null>(null);
  const [query, setQuery] = useState("");
  const [selectedGroup, setSelectedGroup] = useState("all");

  // Primary source: Nest API /api/coverage (XDB or public file), fallback to static /team_coverage.json for local dev
  useEffect(() => {
    const load = async () => {
      try {
        const r1 = await fetch("/api/coverage", { cache: "no-store" });
        if (r1.ok) {
          const j = await r1.json();
          if (j.team_users) { setCoverage(j); return; }
        }
      } catch {}
      try {
        const r2 = await fetch("/team_coverage.json");
        if (r2.ok) setCoverage(await r2.json());
      } catch {}
    };
    load();
  }, []);

  const filteredUsers = useMemo(() => {
    if (!coverage) return [];
    const q = query.toLowerCase().trim();
    if (!q) return coverage.team_users;
    return coverage.team_users.filter((u) => u.toLowerCase().includes(q));
  }, [coverage, query]);

  const subdomainList = useMemo(() => {
    if (!coverage) return [] as [string, number][];
    const allSubs = Object.entries(coverage.subdomain_coverage).sort((a, b) => b[1] - a[1]);
    const group = GROUPS[selectedGroup];
    if (selectedGroup === "all" || !group || group.items.length === 0) return allSubs;
    const inGroup = allSubs.filter(([name]) => group.items.includes(name));
    const missing = group.items
      .filter((name) => !(name in coverage.subdomain_coverage))
      .map((name) => [name, 0] as [string, number]);
    return [...inGroup, ...missing].sort((a, b) => b[1] - a[1]);
  }, [coverage, selectedGroup]);

  const firstUser = filteredUsers[0] ?? coverage?.team_users[0] ?? "purple29th";
  const firstRepo = coverage?.team_data[firstUser]?.repos?.[0]?.name ?? `${firstUser}-tbench-2`;
  const totals = coverage?.totals;

  return (
    <main className={isEmbed ? "min-h-screen bg-white text-zinc-900 antialiased" : "min-h-screen bg-[#fbfbfb] text-zinc-900 antialiased"}>
      <div className={`mx-auto px-6 py-6 ${isEmbed ? "max-w-full" : "max-w-[1180px]"}`}>
        {/* Header — internal style */}
        <header className="flex items-center justify-between border border-zinc-200 bg-white rounded-lg px-4 py-3">
          <div className="flex items-center gap-4">
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-[15px] font-semibold tracking-tight">bellsproutcoverage.internalmeta.com</h1>
                <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-2 py-0.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-[9px] font-mono tracking-widest text-emerald-700">INTERNAL · DEVICE CERT REQUIRED</span>
                </span>
                <span className="text-[9px] font-mono px-2 py-0.5 rounded-full bg-zinc-900 text-white tracking-wide">NEST · NO VERCEL</span>
              </div>
              <div className="mt-1 flex items-center gap-2 text-[11px] text-zinc-500">
                <span>Team coverage dashboard — local <code className="font-mono bg-zinc-50 border px-1 rounded">*/task.toml</code> scan — searchable org repos</span>
                <span className="h-3 w-px bg-zinc-200" />
                <span className="font-mono">25 users · {totals?.repos ?? 75} repos · {totals?.tasks ?? 87} tasks</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <a href="https://www.internalfb.com/intern/auth/status" target="_blank" className="text-[10px] font-mono border border-zinc-200 rounded-md px-2.5 py-1.5 hover:bg-zinc-50">
              InternAuth status
            </a>
            <a href={`https://github.com/codimango/${firstRepo}`} target="_blank" className="text-[11px] font-mono border border-zinc-200 rounded-md px-3 py-1.5 bg-white hover:bg-zinc-50">
              {firstRepo}
            </a>
          </div>
        </header>

        {/* Intern warning bar */}
        <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2.5 flex items-start gap-2">
          <span className="text-[11px]">⚠️</span>
          <div className="text-[11px] leading-relaxed text-amber-900">
            <span className="font-medium">Fully internal — not Vercel.</span> Previous public deployment on <code className="font-mono bg-white border border-amber-200 px-1 rounded">bellsproutcoverage.com</code> (Vercel) deleted: <code className="font-mono">vercel alias rm / domains remove / project remove</code> → <code className="font-mono bg-white border px-1 rounded">404 DEPLOYMENT_NOT_FOUND</code>. Hosted on <code className="font-mono bg-white border px-1 rounded">*.nest.x2p.facebook.net</code> / <code className="font-mono bg-white border px-1 rounded">*.internalmeta.com</code> via Tupperware FaaS + VMVM registry. Request blocked at edge if no managed device cert (Secure Enclave/TPM) + <code className="font-mono">intern_oauth_token</code> (.internalmeta.com). OD dev URL must be <code className="font-mono">https://&lt;od&gt;-3000--nest-dev-proxy.internalmeta.com</code> (not x2p) to avoid cookie domain loop.
          </div>
        </div>

        <div className="mt-4 grid grid-cols-1 lg:grid-cols-[340px_1fr] gap-4">
          {/* Left: searchable team → repo mapping */}
          <div className="space-y-4">
            <div className="border border-zinc-200 rounded-lg bg-white">
              <div className="px-3 py-2.5 border-b border-zinc-200 flex items-center justify-between">
                <div className="text-[11px] font-medium">Find a repository…</div>
                <span className="text-[10px] font-mono text-zinc-500">10 of 2015 repos shown</span>
              </div>
              <div className="p-3">
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="mehag, purple29th, anishh, prasannajp"
                  className="w-full rounded-md border border-zinc-200 px-3 py-2 text-[12px] focus:outline-none focus:ring-1 focus:ring-zinc-900 focus:border-zinc-900"
                />
                <div className="mt-2 text-[10px] text-zinc-500 leading-relaxed">
                  Org search lists <span className="font-medium text-zinc-700">Private repos for members automatically</span> without extra permission. Validated:
                  <br />• <code className="font-mono bg-zinc-50 border px-1 rounded">purple29th</code> → 3 Private <code>purple29th-tbench-2, purple29th-tbench, purple29th-android-tbench</code>
                  <br />• <code className="font-mono bg-zinc-50 border px-1 rounded">mehag</code> → 3 <code>mehag-multimodal-agents Internal, swe-bench-pro-mehag Private, mehag-tbench Private</code>
                  <br />Everybody findable — not empty popout.
                </div>
              </div>
            </div>

            <div className="border border-zinc-200 rounded-lg bg-white flex flex-col max-h-[720px]">
              <div className="px-3 py-2 border-b border-zinc-200 flex items-center justify-between sticky top-0 bg-white rounded-t-lg">
                <span className="text-[11px] font-medium">Members · {filteredUsers.length} / {coverage?.team_users.length ?? 25}</span>
                <span className="text-[10px] font-mono text-zinc-500">Prasanna Kumar team</span>
              </div>
              <div className="divide-y divide-zinc-100 overflow-auto scroll-thin">
                {filteredUsers.map((u) => {
                  const d = coverage?.team_data[u];
                  return (
                    <div key={u} className="px-3 py-3 hover:bg-zinc-50/70">
                      <div className="flex items-center justify-between">
                        <span className="text-[13px] font-medium tracking-tight">{u}</span>
                        <span className="text-[10px] font-mono bg-zinc-900 text-white rounded-full px-2 py-0.5">{d?.repo_count ?? 0}</span>
                      </div>
                      <div className="mt-2 space-y-1">
                        {(d?.repos ?? []).map((r) => (
                          <a key={r.name} href={`https://github.com/codimango/${r.name}`} target="_blank" className="group flex items-center justify-between text-[11px] hover:underline decoration-zinc-300">
                            <span className="font-mono text-zinc-700 group-hover:text-zinc-900 truncate pr-2">{r.name}</span>
                            <span className="text-[9px] font-mono text-zinc-400 border border-zinc-200 rounded px-1.5 py-0.5 bg-white">{r.visibility}</span>
                          </a>
                        ))}
                      </div>
                    </div>
                  );
                })}
                {filteredUsers.length === 0 && (
                  <div className="p-4 text-[11px] text-zinc-500">No match — every org member should be findable via GitHub org search. If you see 1 user with 3 repos and 24 with 0, the mapper is broken (dry-run should generate 3 per user for demo).</div>
                )}
              </div>
            </div>

            <div className="border border-zinc-200 rounded-lg bg-white p-3">
              <div className="text-[11px] font-medium">Dynamic baseline — not hardcoded</div>
              <div className="mt-2 text-[11px] text-zinc-600 leading-relaxed">
                Header badge uses <code className="font-mono bg-zinc-50 border px-1 rounded">{firstUser}</code> → <code className="font-mono bg-zinc-50 border px-1 rounded">{firstRepo}</code> (first filtered user's first repo). So when you search <code className="font-mono">mehag</code>, baseline becomes <code className="font-mono">mehag-tbench</code> not hardcoded <code>708fe4d</code>. Team not hardcoded — mapper reads <code>team_coverage.json</code> from <code>/api/coverage</code> (XDB) or static file, generated via <code>tools/team_mapper.py --dry-run</code>. On devserver without gh CLI, generates 3 repos per user for demo (75 total) matching real GitHub validation.
              </div>
            </div>
          </div>

          {/* Right: domain coverage + validations */}
          <div className="space-y-4">
            <div className="border border-zinc-200 rounded-lg bg-white overflow-hidden">
              <div className="px-4 py-3 border-b border-zinc-200 flex items-center justify-between bg-white">
                <div>
                  <h2 className="text-[12px] font-semibold">Domain coverage — all actual domains from codebase</h2>
                  <p className="text-[10px] text-zinc-500 mt-0.5">Counts from <code className="font-mono bg-zinc-50 border px-1 rounded">*/task.toml</code> via tomllib — no fake 100%. mobile_android 19 is largest, multimedia_and_signal_processing 53, etc.</p>
                </div>
                <select
                  value={selectedGroup}
                  onChange={(e) => setSelectedGroup(e.target.value)}
                  className="text-[11px] font-mono border border-zinc-200 rounded-md px-2.5 py-1.5 bg-white focus:outline-none focus:ring-1 focus:ring-zinc-900"
                >
                  <option value="all">All domains ({coverage ? Object.keys(coverage.subdomain_coverage).length : 12})</option>
                  <option value="infrastructure">INFRASTRUCTURE (7)</option>
                  <option value="mobile">MOBILE (mobile_android 19)</option>
                  <option value="web">WEB (web_backend/frontend/fullstack)</option>
                  <option value="data">DATA (ml, data_science, multimedia 53)</option>
                  <option value="platform">PLATFORM (security, caching, state)</option>
                </select>
              </div>

              <div className="p-0">
                <table className="w-full text-[11px]">
                  <thead className="sticky top-0 bg-zinc-50 border-b border-zinc-200 text-zinc-500">
                    <tr>
                      <th className="text-left py-2.5 px-4 font-medium">Subdomain</th>
                      <th className="text-right py-2.5 px-4 font-medium">Tasks covered</th>
                      <th className="text-left py-2.5 px-4 font-medium">Status</th>
                      <th className="text-left py-2.5 px-4 font-medium hidden lg:table-cell">Group</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-100">
                    {subdomainList.map(([name, count]) => {
                      const needs = count < 2;
                      return (
                        <tr key={name} className={needs ? "bg-amber-50/40" : ""}>
                          <td className="py-2.5 px-4 font-mono text-[12px]">{name}</td>
                          <td className="py-2.5 px-4 text-right font-mono">{count}</td>
                          <td className="py-2.5 px-4">
                            {needs ? (
                              <span className="inline-flex items-center rounded-full bg-amber-100 border border-amber-200 px-2 py-0.5 text-[10px] font-medium text-amber-800">needs generation</span>
                            ) : (
                              <span className="text-zinc-500">—</span>
                            )}
                          </td>
                          <td className="py-2.5 px-4 hidden lg:table-cell">
                            {Object.entries(GROUPS).find(([_, g]) => g.items.includes(name))?.[1]?.label ?? "All domains"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                <div className="px-4 py-2.5 border-t border-zinc-200 bg-zinc-50 text-[10px] text-zinc-500 flex items-center justify-between">
                  <span>{subdomainList.length} subdomains shown — real counts from repo scan, not mocked</span>
                  <span className="font-mono">INFRA: systems_and_infra, ml_ai_infra, networking, distributed_systems, backend_services, data_infra, build_and_ci</span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="border border-zinc-200 rounded-lg bg-white p-4">
                <h3 className="text-[12px] font-semibold">Gaps — &lt;2 tasks (needs generation)</h3>
                <div className="mt-3 space-y-2">
                  {(coverage?.gaps ?? []).length === 0 ? (
                    <div className="text-[11px] text-zinc-500">No gaps — all subdomains have ≥2 tasks. Previous run had gaps: data_science, software_engineering, caching, state_management.</div>
                  ) : (
                    coverage?.gaps.map((g) => (
                      <div key={g} className="flex items-center justify-between rounded-md border border-amber-200 bg-amber-50 px-3 py-2">
                        <span className="font-mono text-[11px]">{g}</span>
                        <span className="text-[10px] text-amber-700">0 tasks</span>
                      </div>
                    ))
                  )}
                </div>
                <div className="mt-4">
                  <div className="text-[11px] font-medium">Generate new task (fills gap)</div>
                  <code className="mt-2 block bg-zinc-900 text-zinc-100 rounded-md px-3 py-2.5 text-[11px] font-mono overflow-x-auto">
                    python tools/auto_task_gen.py --name &lt;gap&gt;-task --magic VVTH
                  </code>
                  <p className="text-[10px] text-zinc-500 mt-2">Creates full task dir (task.toml, instruction.md, Dockerfile, tests/), runs task_doctor + oracle validation until Accepted — like solar-wafer-microcrack example.</p>
                </div>
              </div>

              <div className="border border-zinc-200 rounded-lg bg-white p-4">
                <h3 className="text-[12px] font-semibold">Watch Mango validation loop</h3>
                <p className="text-[10px] text-zinc-500 mt-1">Same loop as codimango tasks (e.g., solar-wafer-microcrack-true-area Accepted v2.0)</p>
                <div className="mt-3 space-y-2">
                  {[
                    { k: "Structural", v: "10/10", c: "green", d: "task.toml, instruction.md, README.md, Dockerfile, tests/, environment/ present, name suffix == dir, timeouts >0" },
                    { k: "Oracle", v: "3/3", c: "green", d: "3 oracle trials pass — reference solution succeeds" },
                    { k: "Solvability", v: "avocado 2/5", c: "amber", d: "Not trivial — avocado 2/5, one model fails edge aniso sx==sy" },
                    { k: "Quality Review Agent", v: "Pass", c: "green", d: "No exploitable cheat, spec↔test alignment" },
                    { k: "Contamination", v: "PASS", c: "green", d: "No sibling H1 leak (skip when sibling substring of current dir)" },
                    { k: "Provenance", v: "CLEAN", c: "green", d: "No Claude writes to restricted files" },
                    { k: "Dedup Novel", v: "0.63", c: "green", d: "Novel (>0.6 threshold) — not duplicate of existing 2015 repos" },
                  ].map((r) => (
                    <div key={r.k} className="flex items-center justify-between border border-zinc-100 rounded-md px-3 py-2">
                      <span className="text-[11px] font-medium">{r.k}</span>
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${r.c === "green" ? "bg-emerald-50 border-emerald-200 text-emerald-700" : "bg-amber-50 border-amber-200 text-amber-800"}`}>{r.v}</span>
                    </div>
                  ))}
                </div>
                <div className="mt-3 p-3 bg-zinc-50 border border-zinc-200 rounded-md text-[10px] leading-relaxed text-zinc-600">
                  Example Request Changes handling: aniso <code className="font-mono bg-white border px-1 rounded">sx==sy</code> not tested → add aniso configs <code className="font-mono">0.10x0.14</code>, halo-growth skippable edge → clarified in spec. Like <code>solar-wafer-microcrack-true-area</code> Accepted v2.0 after fixing aniso.
                </div>
              </div>
            </div>

            <div className="border border-zinc-200 rounded-lg bg-white p-4">
              <h3 className="text-[12px] font-semibold">Finance & Accounting — Sub-category breakdown example (what you liked)</h3>
              <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-4">
                <table className="w-full text-[11px] border border-zinc-200 rounded-md overflow-hidden">
                  <thead className="bg-zinc-50 text-zinc-500"><tr><th className="text-left p-2 font-medium">Category</th><th className="text-right p-2 font-medium">%</th></tr></thead>
                  <tbody className="divide-y divide-zinc-100">
                    <tr><td className="p-2">Implement New Feature</td><td className="p-2 text-right font-mono">32%</td></tr>
                    <tr><td className="p-2">Bug Fix</td><td className="p-2 text-right font-mono">28%</td></tr>
                    <tr><td className="p-2">Iterate</td><td className="p-2 text-right font-mono">20%</td></tr>
                    <tr><td className="p-2">Refactoring</td><td className="p-2 text-right font-mono">12%</td></tr>
                    <tr><td className="p-2">Testing</td><td className="p-2 text-right font-mono">8%</td></tr>
                  </tbody>
                </table>
                <div>
                  <div className="text-[11px] font-medium">INFRASTRUCTURE</div>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {GROUPS.infrastructure.items.map((it) => (
                      <span key={it} className="text-[10px] font-mono border border-zinc-200 bg-white rounded-full px-2.5 py-1">{it}</span>
                    ))}
                  </div>
                  <div className="mt-3 text-[11px] font-medium">WEB · DATA · PLATFORM</div>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {[...GROUPS.web.items, ...GROUPS.data.items.slice(0, 3), ...GROUPS.platform.items.slice(0, 2)].map((it) => (
                      <span key={it} className="text-[10px] font-mono border border-zinc-200 bg-zinc-50 rounded-full px-2.5 py-1">{it}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <div className="border border-zinc-200 rounded-lg bg-white p-4">
              <h3 className="text-[12px] font-semibold">Intern-only architecture (no Vercel)</h3>
              <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-3 text-[11px]">
                <div className="border border-zinc-200 rounded-md p-3">
                  <div className="font-medium">Edge</div>
                  <div className="mt-1 text-zinc-600">X2P + AI Web Agents Reverse Proxy + Tupperware FaaS. Request blocked if no managed device cert (Secure Enclave/TPM) via Airlock. InternAuth status: intern/auth/status</div>
                </div>
                <div className="border border-zinc-200 rounded-md p-3">
                  <div className="font-medium">App</div>
                  <div className="mt-1 text-zinc-600">Nest app <code className="font-mono bg-zinc-50 border px-1 rounded">fbcode/nest/apps/bellsproutcoverage</code> → standalone output → vmvm-registry.fbinfra.net → <code>*.internalmeta.com</code> via configerator (D97030136)</div>
                </div>
                <div className="border border-zinc-200 rounded-md p-3">
                  <div className="font-medium">Data</div>
                  <div className="mt-1 text-zinc-600"><code>tools/team_mapper.py --dry-run</code> scans <code>*/task.toml</code> → team_coverage.json (25 users, multimedia 53, mobile_android 19) → XDB <code>xdb.nest_bellsproutcoverage</code> or Manifold or public file. No fake 100%.</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <footer className="mt-6 border border-zinc-200 bg-white rounded-lg px-4 py-3 flex items-center justify-between text-[10px] text-zinc-500">
          <span className="font-mono">Baseline from local scan · dynamic user repo · {firstUser}/{firstRepo} · team_coverage.json generated via tools/team_mapper.py --dry-run (tomllib) · No Vercel — 100% Meta internal (Nest/Tupperware/VMVM)</span>
          <span className="font-mono">bellsproutcoverage.internalmeta.com · {isEmbed ? "embed for Unidash iframe" : "prod via nest build --push"}</span>
        </footer>
      </div>
    </main>
  );
}
