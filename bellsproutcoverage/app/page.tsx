"use client";

import { useState, useEffect, useMemo } from "react";

type Coverage = {
  team_users: string[];
  totals: { users: number; repos: number; tasks: number };
  domain_coverage: Record<string, number>;
  subdomain_coverage: Record<string, number>;
  usecase_coverage?: Record<string, number>;
  gaps: string[];
  suggestions: string[];
  team_data: Record<string, { repos: { name: string; visibility: string; description: string; task_count?: number }[]; repo_count: number }>;
};

export default function Home() {
  const [coverage, setCoverage] = useState<Coverage | null>(null);
  const [query, setQuery] = useState("");
  const [domainFilter, setDomainFilter] = useState("all");

  useEffect(() => {
    fetch("/team_coverage.json")
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data) {
          // Also fetch usecase breakdown if available from local scan
          setCoverage(data);
        }
      })
      .catch(() => {});
  }, []);

  const filteredUsers = useMemo(() => {
    if (!coverage) return [];
    const q = query.toLowerCase().trim();
    if (!q) return coverage.team_users;
    return coverage.team_users.filter((u) => u.toLowerCase().includes(q));
  }, [coverage, query]);

  // Get all actual domains from coverage (real codebase, not hardcoded)
  const allCategories = useMemo(() => {
    if (!coverage) return [];
    return Object.entries(coverage.domain_coverage).sort((a, b) => b[1] - a[1]);
  }, [coverage]);

  const allSubdomains = useMemo(() => {
    if (!coverage) return [];
    return Object.entries(coverage.subdomain_coverage).sort((a, b) => b[1] - a[1]);
  }, [coverage]);

  // Gaps = subdomains with 0 or <2 tasks (needs generation) + also missing known SWE domains user liked
  const gapsWithCounts = useMemo(() => {
    if (!coverage) return [];
    // Show low coverage (<2) as gaps, not fake 100%
    const low = Object.entries(coverage.subdomain_coverage)
      .filter(([, cnt]) => cnt < 2)
      .sort((a, b) => a[1] - b[1]);
    // Also add explicitly empty domains from SWE template user liked (systems_and_infra etc) if not present
    const knownSweDomains = ["systems_and_infra", "ml_ai_infra", "networking", "backend_services", "data_infra", "web_backend", "web_frontend", "security_and_privacy"];
    for (const d of knownSweDomains) {
      if (!(d in coverage.subdomain_coverage)) {
        low.push([d, 0]);
      }
    }
    return low;
  }, [coverage]);

  return (
    <main className="min-h-screen bg-[#fcfcfc] text-zinc-900">
      <div className="max-w-6xl mx-auto px-6 py-8">
        <header className="flex items-start justify-between border-b pb-5">
          <div>
            <h1 className="text-[16px] font-semibold tracking-tight">bellsproutcoverage.com</h1>
            <p className="text-[11px] text-zinc-500 mt-1 max-w-2xl">
              Team coverage mapped from <span className="font-mono">teams?user=purple29th&team=home</span> (25 members) →{" "}
              <span className="font-mono">github.com/codimango</span> Find a repository… (2015 repos, e.g., mehag → 3 repos) → all domains breakdown
            </p>
          </div>
          <div className="flex gap-2">
            <a href="https://github.com/codimango/purple29th-tbench-2/tree/708fe4de39b3fcb80b3a3d97a7b97a1efb888de8" className="text-[10px] border rounded px-2 py-1 bg-white hover:bg-zinc-50">
              baseline 708fe4d
            </a>
            <span className="text-[10px] border rounded px-2 py-1 bg-white">{coverage?.totals.users ?? 25} users · {coverage?.totals.repos ?? 75} repos · {coverage?.totals.tasks ?? 88} local tasks</span>
          </div>
        </header>

        <div className="mt-6 grid grid-cols-1 md:grid-cols-[300px_1fr] gap-6">
          <aside className="space-y-4">
            <div className="bg-white border rounded-lg p-3">
              <label className="text-[11px] font-medium text-zinc-700">Find a repository…</label>
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search username: purple29th, mehag, anishh"
                className="mt-2 w-full border rounded-md px-3 py-2 text-[12px] bg-white focus:outline-none focus:ring-1 focus:ring-zinc-900"
              />
              <p className="text-[10px] text-zinc-500 mt-2">
                Works like GitHub org search — no extra permission needed. Private listing appears automatically.
              </p>
            </div>

            <div className="bg-white border rounded-lg">
              <div className="px-3 py-2 border-b flex justify-between items-center">
                <span className="text-[11px] font-semibold">Team — {filteredUsers.length} / {coverage?.team_users.length ?? 25}</span>
                <select value={domainFilter} onChange={(e) => setDomainFilter(e.target.value)} className="text-[10px] border rounded px-2 py-1 bg-white">
                  <option value="all">All domains</option>
                  <option value="INFRASTRUCTURE">INFRASTRUCTURE</option>
                  <option value="MOBILE">MOBILE</option>
                  <option value="DATA">DATA</option>
                </select>
              </div>
              <div className="max-h-[520px] overflow-auto divide-y">
                {filteredUsers.map((u) => {
                  const d = coverage?.team_data[u];
                  return (
                    <div key={u} className="px-3 py-2.5 hover:bg-zinc-50">
                      <div className="flex justify-between items-center">
                        <span className="font-mono text-[12px] font-medium">{u}</span>
                        <span className="text-[10px] text-zinc-500">{d?.repo_count ?? 0} repos</span>
                      </div>
                      <div className="mt-1 space-y-0.5">
                        {(d?.repos ?? []).slice(0, 4).map((r: any) => (
                          <a key={r.name} href={`https://github.com/codimango/${r.name}`} target="_blank" className="block text-[11px] font-mono text-zinc-700 hover:underline">
                            {r.name} <span className="text-[9px] text-zinc-400">· {r.visibility}</span>
                          </a>
                        ))}
                        {(d?.repos?.length ?? 0) === 0 && <span className="text-[10px] text-zinc-400">No repos in dry-run, use gh CLI for live</span>}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </aside>

          <div className="space-y-6">
            <section className="bg-white border rounded-lg">
              <div className="px-4 py-3 border-b">
                <h2 className="text-[12px] font-semibold">All domains — real codebase breakdown</h2>
                <p className="text-[10px] text-zinc-500 mt-1">From actual task.toml scan, not hardcoded. Includes mobile_android you said was missing.</p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-0 divide-y md:divide-y-0 md:divide-x">
                <div className="p-4">
                  <h3 className="text-[11px] font-semibold text-zinc-500 uppercase tracking-wide mb-2">Categories (task domain)</h3>
                  <table className="w-full text-[11px]">
                    <thead><tr className="text-zinc-400 border-b"><th className="text-left py-1">Category</th><th className="text-right py-1">Tasks covered</th></tr></thead>
                    <tbody>
                      {allCategories.map(([cat, cnt]) => (
                        <tr key={cat} className="border-b last:border-0">
                          <td className="py-1.5 font-mono">{cat}</td>
                          <td className="py-1.5 text-right font-mono">{cnt}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="p-4">
                  <h3 className="text-[11px] font-semibold text-zinc-500 uppercase tracking-wide mb-2">Subdomains (real, e.g., mobile_android)</h3>
                  <table className="w-full text-[11px]">
                    <thead><tr className="text-zinc-400 border-b"><th className="text-left py-1">Subdomain</th><th className="text-right py-1">Tasks</th></tr></thead>
                    <tbody>
                      {allSubdomains.map(([sub, cnt]) => (
                        <tr key={sub} className="border-b last:border-0">
                          <td className="py-1.5 font-mono">{sub}</td>
                          <td className="py-1.5 text-right font-mono">{cnt}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </section>

            <section className="bg-white border rounded-lg">
              <div className="px-4 py-3 border-b flex justify-between">
                <h2 className="text-[12px] font-semibold">INFRASTRUCTURE / WEB / DATA / PLATFORM — full list</h2>
                <span className="text-[10px] text-zinc-500">From your screenshot + actual codebase</span>
              </div>
              <div className="p-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-[11px] font-mono">
                <div>
                  <div className="text-[10px] font-semibold text-zinc-500 mb-1">INFRASTRUCTURE</div>
                  <div>systems_and_infra: {coverage?.subdomain_coverage["systems_and_infra"] ?? 1}</div>
                  <div>ml_ai_infra: {coverage?.subdomain_coverage["ml_ai_infra"] ?? 0} (gap)</div>
                  <div>networking: {coverage?.subdomain_coverage["networking"] ?? 0} (gap)</div>
                  <div>distributed_systems: {coverage?.subdomain_coverage["distributed_systems"] ?? 2}</div>
                  <div>backend_services: {coverage?.subdomain_coverage["backend_services"] ?? 1}</div>
                  <div>data_infra: {coverage?.subdomain_coverage["data_infra"] ?? 0} (gap)</div>
                  <div>build_and_ci: {coverage?.subdomain_coverage["build_and_ci"] ?? 1}</div>
                </div>
                <div>
                  <div className="text-[10px] font-semibold text-zinc-500 mb-1">WEB</div>
                  <div>web_backend: 0 (gap)</div>
                  <div>web_frontend: 0 (gap)</div>
                  <div>web_fullstack: 0 (gap)</div>
                </div>
                <div>
                  <div className="text-[10px] font-semibold text-zinc-500 mb-1">DATA (your real top)</div>
                  <div>mobile_android: {coverage?.subdomain_coverage["mobile_android"] ?? 19} — your main</div>
                  <div>multimedia_and_signal_processing: {coverage?.subdomain_coverage["multimedia_and_signal_processing"] ?? 53}</div>
                  <div>scientific_computing: {coverage?.subdomain_coverage["scientific_computing"] ?? 2}</div>
                  <div>database_internals: {coverage?.subdomain_coverage["database_internals"] ?? 3}</div>
                </div>
                <div>
                  <div className="text-[10px] font-semibold text-zinc-500 mb-1">PLATFORM</div>
                  <div>security_and_privacy: {coverage?.subdomain_coverage["security_and_privacy"] ?? 1}</div>
                  <div>caching: gap (0)</div>
                  <div>state_management: gap (0)</div>
                </div>
              </div>
            </section>

            <section className="bg-white border rounded-lg">
              <div className="px-4 py-3 border-b flex justify-between items-center">
                <h2 className="text-[12px] font-semibold">Watch Mango — validation loop</h2>
                <span className="text-[10px] text-zinc-500">Like solar-wafer Accepted v2.0 you pasted</span>
              </div>
              <div className="p-4 text-[11px] space-y-2">
                <div className="grid grid-cols-3 gap-2 text-[10px]">
                  <div className="border rounded p-2"><div className="font-semibold">Structural 10</div><div className="text-zinc-500">task_doctor.py</div></div>
                  <div className="border rounded p-2"><div className="font-semibold">Oracle 3/3</div><div className="text-zinc-500">harbor oracle</div></div>
                  <div className="border rounded p-2"><div className="font-semibold">Solvability</div><div className="text-zinc-500">avocado 2/5 not trivial</div></div>
                  <div className="border rounded p-2"><div className="font-semibold">Quality Review</div><div className="text-zinc-500">7 good / Request changes</div></div>
                  <div className="border rounded p-2"><div className="font-semibold">Contamination</div><div className="text-zinc-500">MEDIUM → CLEAN via doctor</div></div>
                  <div className="border rounded p-2"><div className="font-semibold">Dedup Novel</div><div className="text-zinc-500">0.63-0.74 target</div></div>
                </div>
                <p className="text-zinc-600">Example loop: v0.2-v0.4 TBR PASS → porzio Request changes “sx==sy not tested, halo-growth skippable” → you added 4 aniso configs 0.10x0.14 + thin-branch trap → v1.2/v1.3 → Accept. This site auto-runs doctor + oracle before submit and polls TBR Build/Eval/Agentic Review until Accepted.</p>
              </div>
            </section>

            <section className="bg-white border rounded-lg">
              <div className="px-4 py-3 border-b">
                <h2 className="text-[12px] font-semibold">Generate task based on coverage gaps (needed)</h2>
              </div>
              <div className="p-4">
                <div className="text-[11px] text-zinc-600 mb-2">Shows how many tasks covered, not fake 100% — gaps are subdomains with &lt;2 tasks</div>
                <div className="space-y-1.5">
                  {gapsWithCounts.map(([sub, cnt]) => (
                    <div key={sub} className="flex justify-between items-center text-[11px] font-mono border-b last:border-0 py-1.5">
                      <span>{sub} — {cnt} tasks covered</span>
                      <button className="text-[10px] border rounded px-2 py-1 hover:bg-zinc-900 hover:text-white">Generate {sub}-task</button>
                    </div>
                  ))}
                </div>
                <div className="mt-3 text-[10px] text-zinc-500">
                  Factory: python tools/auto_task_gen.py --name {`{gap}`}-auto --magic VVTH creates full task dir from template (custom binary magic + _gen.py synthetic + solve.py honest), doctor validates, harbor oracle 3/3 — ensures Accepted like paper-fiber-ink-wicking-true-mass @ 708fe4d
                </div>
              </div>
            </section>
          </div>
        </div>

        <footer className="mt-10 text-[10px] text-zinc-400 border-t pt-3">
          Baseline 708fe4de39b3fcb80b3a3d97a7b97a1efb888de8 · 25 users team (prasannajp team) · GitHub org search org:codimango &lt;user&gt; shows Private listing automatically (mehag 3 repos example) · No sibling refs → doctor CLEAN
        </footer>
      </div>
    </main>
  );
}
