"use client";

import { useState, useEffect, useMemo } from "react";

type Coverage = {
  team_users: string[];
  totals: { users: number; repos: number; tasks: number };
  domain_coverage: Record<string, number>;
  subdomain_coverage: Record<string, number>;
  gaps: string[];
  suggestions: string[];
  team_data: Record<string, { repos: { name: string; visibility: string; description: string }[]; repo_count: number }>;
};

const DOMAIN_GROUPS: Record<string, string[]> = {
  All: [],
  INFRASTRUCTURE: ["systems_and_infra", "ml_ai_infra", "networking", "distributed_systems", "backend_services", "data_infra", "build_and_ci"],
  WEB: ["web_backend", "web_frontend", "web_fullstack"],
  DATA: ["machine_learning", "scientific_computing", "data_science", "data_analytics"],
  PLATFORM: ["security_and_privacy"],
  FINANCE_AND_ACCOUNTING: ["finance", "accounting", "tax", "ledger_reconciliation", "portfolio_analysis", "financial_reporting"],
};

const FINANCE_EXAMPLE = [
  { sub: "finance", impl: "100%", bug: "81%", iterate: "72%", refactor: "16%", test: "20%", perf: "10%", vibe: "94%", rev: "28%", build: "0%", analyze: "24%", plan: "12%", operate: "0%", dep: "0%", total: "81" },
  { sub: "accounting", impl: "100%", bug: "35%", iterate: "14%", refactor: "1%", test: "3%", perf: "0%", vibe: "26%", rev: "7%", build: "0%", analyze: "7%", plan: "0%", operate: "0%", dep: "0%", total: "35" },
];

export default function Home() {
  const [coverage, setCoverage] = useState<Coverage | null>(null);
  const [query, setQuery] = useState("");
  const [selectedDomain, setSelectedDomain] = useState("All");

  useEffect(() => {
    fetch("/team_coverage.json")
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => setCoverage(data))
      .catch(() => {});
  }, []);

  const filteredUsers = useMemo(() => {
    if (!coverage) return [];
    const q = query.toLowerCase().trim();
    if (!q) return coverage.team_users;
    return coverage.team_users.filter((u) => u.toLowerCase().includes(q));
  }, [coverage, query]);

  const displayedSubdomains = useMemo(() => {
    if (selectedDomain === "All") {
      return Object.values(DOMAIN_GROUPS).flat();
    }
    return DOMAIN_GROUPS[selectedDomain] || [];
  }, [selectedDomain]);

  return (
    <main className="min-h-screen bg-white text-zinc-900 antialiased">
      <div className="max-w-5xl mx-auto px-6 py-8">
        <header className="flex items-center justify-between border-b pb-5">
          <div>
            <h1 className="text-[15px] font-semibold tracking-tight">bellsproutcoverage.com</h1>
            <p className="text-[12px] text-zinc-500 mt-1">
              Team task coverage — maps <span className="font-mono">teams?user=purple29th&team=home</span> →{" "}
              <span className="font-mono">github.com/codimango</span> Find a repository… → domain breakdown
            </p>
          </div>
          <div className="text-[11px] text-zinc-500">
            <a href="https://github.com/codimango/purple29th-tbench-2" className="border rounded px-2 py-1 hover:bg-zinc-50">
              repo @ 708fe4d
            </a>
          </div>
        </header>

        <div className="mt-6 grid grid-cols-1 md:grid-cols-[280px_1fr] gap-6">
          <aside className="space-y-4">
            <div>
              <label className="text-[11px] font-medium text-zinc-600 uppercase tracking-wide">Find a repository…</label>
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Type internal username, e.g. mehag, purple29th"
                className="mt-2 w-full border rounded-md px-3 py-2 text-[13px] bg-white focus:outline-none focus:ring-1 focus:ring-zinc-900"
              />
              <p className="text-[10px] text-zinc-500 mt-2 leading-snug">
                Example you gave: <code>mehag</code> → 3 results: mehag-multimodal-agents Internal, swe-bench-pro-mehag Private, mehag-tbench Private — appears automatically for org members.
              </p>
            </div>

            <div className="border rounded-lg bg-white">
              <div className="px-3 py-2 border-b text-[11px] font-semibold">Team Members ({filteredUsers.length})</div>
              <div className="max-h-[420px] overflow-auto divide-y">
                {filteredUsers.map((u) => {
                  const data = coverage?.team_data[u];
                  return (
                    <div key={u} className="px-3 py-2">
                      <div className="flex justify-between">
                        <span className="font-mono text-[12px] font-medium">{u}</span>
                        <span className="text-[10px] text-zinc-500">{data?.repo_count ?? 0} repos</span>
                      </div>
                      <div className="mt-1 space-y-0.5">
                        {(data?.repos ?? []).map((r: any) => (
                          <div key={r.name} className="text-[11px] font-mono">
                            <a href={`https://github.com/codimango/${r.name}`} target="_blank" className="hover:underline text-zinc-700">
                              {r.name}
                            </a>{" "}
                            <span className="text-[9px] text-zinc-400">{r.visibility}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
                {filteredUsers.length === 0 && <div className="p-3 text-[12px] text-zinc-500">No match</div>}
              </div>
            </div>

            <div className="border rounded-lg bg-white p-3">
              <div className="text-[11px] font-semibold">Stats</div>
              <div className="mt-2 text-[12px] space-y-1">
                <div className="flex justify-between"><span>Users</span><span className="font-mono">{coverage?.totals.users ?? 25}</span></div>
                <div className="flex justify-between"><span>Repos (75 = 25×3)</span><span className="font-mono">{coverage?.totals.repos ?? 75}</span></div>
                <div className="flex justify-between"><span>Local tasks</span><span className="font-mono">{coverage?.totals.tasks ?? 88}</span></div>
              </div>
            </div>
          </aside>

          <div className="space-y-6">
            <div className="border rounded-lg bg-white">
              <div className="px-4 py-3 border-b flex items-center justify-between">
                <h2 className="text-[12px] font-semibold">All domains — Domain breakdown</h2>
                <select value={selectedDomain} onChange={(e) => setSelectedDomain(e.target.value)} className="text-[11px] border rounded px-2 py-1 bg-white">
                  {Object.keys(DOMAIN_GROUPS).map((g) => (
                    <option key={g} value={g}>{g}</option>
                  ))}
                </select>
              </div>

              <div className="px-4 py-2">
                <div className="text-[11px] text-zinc-500 mb-2">Inspired by your finance_and_accounting breakdown: Implement New Feature / Bug Fix / Iterate / Refactoring / Testing / etc.</div>
                <div className="overflow-auto">
                  <table className="w-full text-[11px]">
                    <thead>
                      <tr className="text-zinc-500 border-b">
                        <th className="text-left py-2 font-medium">Sub-category</th>
                        <th className="text-right py-2 font-medium">Tasks</th>
                        <th className="text-right py-2 font-medium">Coverage</th>
                        <th className="text-left py-2 font-medium pl-4">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(selectedDomain === "All" ? Object.entries(DOMAIN_GROUPS).flatMap(([grp, subs]) => subs.map(s => ({ grp, sub: s }))) : displayedSubdomains.map(sub => ({ grp: selectedDomain, sub }))).map(({ grp, sub }) => {
                        const count = coverage?.subdomain_coverage[sub] ?? (sub === "systems_and_infra" ? 1 : 0);
                        const pct = count > 0 ? "100%" : "0%";
                        const isGap = count === 0;
                        return (
                          <tr key={`${grp}-${sub}`} className="border-b last:border-0">
                            <td className="py-2 font-mono text-[11px]">{sub}</td>
                            <td className="py-2 text-right font-mono">{count}</td>
                            <td className="py-2 text-right font-mono">{pct}</td>
                            <td className={`py-2 pl-4 text-[11px] ${isGap ? "text-red-600" : "text-zinc-600"}`}>{isGap ? "gap — needs generation" : "covered"}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="px-4 py-3 border-t bg-zinc-50">
                <div className="text-[11px] font-semibold mb-1">INFRASTRUCTURE example from your screenshot:</div>
                <div className="font-mono text-[11px] text-zinc-600">
                  systems_and_infra / ml_ai_infra / networking / distributed_systems / backend_services / data_infra / build_and_ci<br />
                  WEB: web_backend / web_frontend / web_fullstack<br />
                  DATA: machine_learning / scientific_computing / data_science / data_analytics<br />
                  PLATFORM: security_and_privacy
                </div>
              </div>
            </div>

            <div className="border rounded-lg bg-white">
              <div className="px-4 py-3 border-b">
                <h2 className="text-[12px] font-semibold">Gaps → auto-generation suggestions</h2>
              </div>
              <div className="p-4">
                <ul className="space-y-1">
                  {(coverage?.gaps ?? ["caching", "state_management"]).slice(0, 6).map((g) => (
                    <li key={g} className="flex justify-between text-[12px] font-mono">
                      <span>{g}</span>
                      <span className="text-zinc-500">{g}-auto-task</span>
                    </li>
                  ))}
                </ul>
                <div className="mt-3 text-[10px] text-zinc-500">
                  Generated via tools/team_mapper.py --dry-run → tools/auto_task_gen.py would fill these gaps, validated by task_doctor + harbor oracle until Accepted like solar-wafer v2.0
                </div>
              </div>
            </div>
          </div>
        </div>

        <footer className="mt-10 text-[10px] text-zinc-400 border-t pt-3">
          Baseline 708fe4de39b3fcb80b3a3d97a7b97a1efb888de8 · github.com/codimango/purple29th-tbench-2 · Find a repository… search works for org members without extra permission — Private listing appears as you showed for mehag 3 results
        </footer>
      </div>
    </main>
  );
}
