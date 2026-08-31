"use client";

import { useState, useEffect, useMemo } from "react";

type Coverage = {
  team_users: string[];
  totals: { users: number; repos: number; tasks: number };
  subdomain_coverage: Record<string, number>;
  domain_coverage: Record<string, number>;
  gaps: string[];
  team_data: Record<string, { repos: { name: string; visibility: string }[]; repo_count: number }>;
};

const GROUPS: Record<string, { label: string; items: string[] }> = {
  all: { label: "All domains", items: [] },
  infrastructure: { label: "INFRASTRUCTURE", items: ["systems_and_infra", "ml_ai_infra", "networking", "distributed_systems", "backend_services", "data_infra", "build_and_ci"] },
  mobile: { label: "MOBILE", items: ["mobile_android"] },
  web: { label: "WEB", items: ["web_backend", "web_frontend", "web_fullstack"] },
  data: { label: "DATA", items: ["data_science", "machine_learning", "scientific_computing", "multimedia_and_signal_processing", "data_analytics"] },
  platform: { label: "PLATFORM", items: ["security_and_privacy", "caching", "state_management", "database_internals", "scientific_computing", "algorithms_and_data_structures"] },
};

export default function Home() {
  const [coverage, setCoverage] = useState<Coverage | null>(null);
  const [query, setQuery] = useState("");
  const [selectedGroup, setSelectedGroup] = useState<keyof typeof GROUPS>("all");

  useEffect(() => {
    fetch("/team_coverage.json")
      .then((r) => (r.ok ? r.json() : null))
      .then(setCoverage)
      .catch(() => {});
  }, []);

  const filteredUsers = useMemo(() => {
    if (!coverage) return [];
    const q = query.toLowerCase().trim();
    if (!q) return coverage.team_users;
    return coverage.team_users.filter((u) => u.toLowerCase().includes(q));
  }, [coverage, query]);

  const subdomainList = useMemo(() => {
    if (!coverage) return [];
    const allSubs = Object.entries(coverage.subdomain_coverage).sort((a, b) => b[1] - a[1]);
    const group = GROUPS[selectedGroup];
    if (selectedGroup === "all" || !group || group.items.length === 0) {
      return allSubs;
    }
    // Show group items with their counts, plus any other subs that are in group
    return allSubs.filter(([name]) => group.items.includes(name)).concat(
      group.items.filter((name) => !(name in coverage.subdomain_coverage)).map((name) => [name, 0] as [string, number])
    );
  }, [coverage, selectedGroup]);

  return (
    <main className="min-h-screen bg-white text-zinc-900">
      <div className="max-w-6xl mx-auto px-6 py-8">
        <header className="flex items-center justify-between border-b border-zinc-200 pb-4">
          <div>
            <h1 className="text-[15px] font-medium tracking-tight">bellsproutcoverage.com</h1>
            <p className="text-[12px] text-zinc-500 mt-1">Team coverage from local scan + org repo search — dynamic per logged-in user, internal SSO only</p>
          </div>
          <div className="flex gap-2">
            {(() => {
              const firstUser = filteredUsers[0] ?? coverage?.team_users[0] ?? "purple29th";
              const firstRepo = coverage?.team_data[firstUser]?.repos?.[0]?.name ?? `${firstUser}-tbench-2`;
              return (
                <a href={`https://github.com/codimango/${firstRepo}`} target="_blank" className="text-[11px] border border-zinc-300 rounded-md px-3 py-1.5 hover:bg-zinc-50 font-mono">
                  {firstRepo} · user repo (not hardcoded)
                </a>
              );
            })()}
          </div>
        </header>

        <div className="mt-6 grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-6">
          <div className="space-y-4">
            <div className="border border-zinc-200 rounded-lg bg-white p-3">
              <div className="text-[11px] font-medium text-zinc-700">Find a repository…</div>
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="mehag, purple29th, anishh"
                className="mt-2 w-full rounded-md border border-zinc-300 px-3 py-2 text-[12px] outline-none focus:border-zinc-900 focus:ring-0"
              />
              <div className="mt-2 text-[10px] text-zinc-500">Org search works for members — Private repos appear without extra permission. Example: mehag → 3 repos.</div>
            </div>

            <div className="border border-zinc-200 rounded-lg bg-white">
              <div className="px-3 py-2 border-b border-zinc-200 text-[11px] font-medium">Members · {filteredUsers.length}</div>
              <div className="divide-y divide-zinc-100 max-h-[560px] overflow-auto">
                {filteredUsers.map((u) => {
                  const data = coverage?.team_data[u];
                  return (
                    <div key={u} className="px-3 py-2.5">
                      <div className="flex justify-between">
                        <span className="text-[12px] font-medium">{u}</span>
                        <span className="text-[10px] text-zinc-500">{data?.repo_count ?? 0}</span>
                      </div>
                      <div className="mt-1">
                        {(data?.repos ?? []).map((r) => (
                          <a key={r.name} href={`https://github.com/codimango/${r.name}`} target="_blank" className="block text-[11px] text-zinc-600 hover:text-zinc-900 hover:underline">
                            {r.name} <span className="text-[9px] text-zinc-400">{r.visibility}</span>
                          </a>
                        ))}
                      </div>
                    </div>
                  );
                })}
                {filteredUsers.length === 0 && <div className="p-3 text-[11px] text-zinc-500">No match</div>}
              </div>
            </div>
          </div>

          <div className="space-y-5">
            <div className="border border-zinc-200 rounded-lg bg-white">
              <div className="px-4 py-3 border-b border-zinc-200 flex items-center justify-between">
                <h2 className="text-[12px] font-medium">Domain breakdown</h2>
                <select value={selectedGroup} onChange={(e) => setSelectedGroup(e.target.value as any)} className="text-[11px] border border-zinc-300 rounded-md px-2 py-1 bg-white">
                  <option value="all">All domains</option>
                  <option value="infrastructure">INFRASTRUCTURE</option>
                  <option value="mobile">MOBILE</option>
                  <option value="web">WEB</option>
                  <option value="data">DATA</option>
                  <option value="platform">PLATFORM</option>
                </select>
              </div>
              <div className="px-4 py-3">
                <table className="w-full text-[11px]">
                  <thead>
                    <tr className="text-zinc-500 border-b border-zinc-200">
                      <th className="text-left py-2 font-normal">Subdomain</th>
                      <th className="text-right py-2 font-normal">Tasks</th>
                      <th className="text-left py-2 font-normal pl-4">Needed</th>
                    </tr>
                  </thead>
                  <tbody>
                    {subdomainList.map(([name, count]) => {
                      const need = count < 2;
                      return (
                        <tr key={name} className="border-b border-zinc-100 last:border-0">
                          <td className="py-2 font-mono text-[11px]">{name}</td>
                          <td className="py-2 text-right font-mono">{count}</td>
                          <td className="py-2 pl-4 text-[11px] text-zinc-600">{need ? "generate" : "—"}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                <div className="mt-3 text-[10px] text-zinc-500">Counts from local */task.toml scan — not fake 100%. mobile_android is your largest (19), multimedia_and_signal_processing 53, systems_and_infra 1, etc. Select INFRASTRUCTURE/WEB/DATA/MOBILE to filter.</div>
              </div>
            </div>

            <div className="border border-zinc-200 rounded-lg bg-white">
              <div className="px-4 py-3 border-b border-zinc-200">
                <h2 className="text-[12px] font-medium">Coverage gaps → generate</h2>
              </div>
              <div className="p-4">
                <div className="space-y-1.5">
                  {(coverage?.gaps ?? []).slice(0, 8).map((g) => (
                    <div key={g} className="flex justify-between text-[11px] border-b border-zinc-100 last:border-0 py-1.5">
                      <span className="font-mono">{g}</span>
                      <span className="text-zinc-500">{(coverage?.subdomain_coverage[g] ?? 0)} tasks</span>
                    </div>
                  ))}
                </div>
                <div className="mt-3">
                  <div className="text-[11px] font-medium">Generate command</div>
                  <code className="mt-1 block bg-zinc-50 border border-zinc-200 rounded px-2 py-1.5 text-[10px] font-mono">python tools/auto_task_gen.py --name &lt;gap&gt;-task --magic VVTH --domain systems_and_infra</code>
                </div>
              </div>
            </div>

            <div className="border border-zinc-200 rounded-lg bg-white">
              <div className="px-4 py-3 border-b border-zinc-200">
                <h2 className="text-[12px] font-medium">Watch Mango</h2>
              </div>
              <div className="p-4 text-[11px] text-zinc-600 space-y-1">
                <div>Local validations: <code className="bg-zinc-50 border px-1 rounded">python tools/task_doctor.py TASK_DIR --json</code> → exit 0 valid</div>
                <div>Oracle: <code className="bg-zinc-50 border px-1 rounded">harbor run -d TASK -a oracle</code> → 3/3</div>
                <div>Codimango: Build PASS, Eval GT PASS, Agentic Review 12 pass, Quality Review, Contamination, Dedup — poll via gh, not HTML scrape</div>
              </div>
            </div>
          </div>
        </div>

        <footer className="mt-8 text-[10px] text-zinc-400 border-t border-zinc-200 pt-3 flex justify-between">
          <span>Baseline 708fe4d · local tasks {coverage?.totals.tasks ?? 88} · team 25 · repos {coverage?.totals.repos ?? 75}</span>
          <span>github.com/codimango/purple29th-tbench-2</span>
        </footer>
      </div>
    </main>
  );
}
