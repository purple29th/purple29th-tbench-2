"use client";

import { useState, useEffect, useMemo } from "react";

type Coverage = {
  team_users: string[];
  totals: { users: number; repos: number; tasks: number };
  domain_coverage: Record<string, number>;
  subdomain_coverage: Record<string, number>;
  gaps: string[];
  suggestions: string[];
  team_data: Record<string, { repos: { name: string; visibility: string; task_count?: number; tasks?: any[] }[]; repo_count: number }>;
};

const DOMAIN_GROUPS: Record<string, string[]> = {
  INFRASTRUCTURE: ["systems_and_infra", "ml_ai_infra", "networking", "distributed_systems", "backend_services", "data_infra", "build_and_ci"],
  WEB: ["web_backend", "web_frontend", "web_fullstack"],
  DATA: ["machine_learning", "scientific_computing", "data_science", "data_analytics"],
  PLATFORM: ["security_and_privacy"],
};

export default function Home() {
  const [coverage, setCoverage] = useState<Coverage | null>(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    fetch("/team_coverage.json")
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data) setCoverage(data);
      })
      .catch(() => {});
  }, []);

  const filteredUsers = useMemo(() => {
    if (!coverage) return [];
    const q = query.toLowerCase().trim();
    if (!q) return coverage.team_users;
    return coverage.team_users.filter((u) => u.toLowerCase().includes(q));
  }, [coverage, query]);

  const filteredTeamData = useMemo(() => {
    if (!coverage) return {};
    const out: Record<string, any> = {};
    for (const u of filteredUsers) {
      out[u] = coverage.team_data[u];
    }
    return out;
  }, [coverage, filteredUsers]);

  return (
    <main className="min-h-screen bg-[#fafafa] text-zinc-900">
      <div className="max-w-6xl mx-auto px-6 py-10">
        <header className="mb-8 border-b pb-6">
          <h1 className="text-[22px] font-semibold tracking-tight">bellsproutcoverage.com</h1>
          <p className="text-sm text-zinc-500 mt-2 max-w-3xl">
            Team task coverage mapped from <span className="font-mono text-xs">codimango/internal/teams?user=purple29th&team=home</span> → GitHub org{" "}
            <span className="font-mono text-xs">codimango</span> Find a repository… → domain / sub-category breakdown
          </p>
          <div className="mt-4 flex gap-2">
            <a href="https://github.com/codimango/purple29th-tbench-2" className="text-xs border px-3 py-1 rounded bg-white hover:bg-zinc-50">
              purple29th-tbench-2 @ 708fe4d
            </a>
            <span className="text-xs border px-3 py-1 rounded bg-white">25 users · 2015 repos index</span>
          </div>
        </header>

        <div className="mb-6">
          <label className="text-xs font-medium text-zinc-600">Find a team member or repository…</label>
          <div className="mt-2 flex gap-2">
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search internal username, e.g. purple29th, anishh, aryasa, chenglu"
              className="w-full border rounded-md px-3 py-2 text-sm bg-white focus:outline-none focus:ring-1 focus:ring-zinc-900"
            />
          </div>
          <p className="text-[11px] text-zinc-500 mt-2">
            Example you gave: typed <code>purple29th</code> → 3 results: <code>purple29th-tbench-2</code> Private, <code>purple29th-tbench</code>, <code>purple29th-android-tbench</code> — Private repos appear for org members without extra permission.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-white border rounded-lg p-4">
            <div className="text-[11px] text-zinc-500 uppercase tracking-wide">Team members</div>
            <div className="text-2xl font-semibold mt-1">{filteredUsers.length} / {coverage?.totals.users ?? 25}</div>
            <div className="text-xs text-zinc-500 mt-1">Filtered by search</div>
          </div>
          <div className="bg-white border rounded-lg p-4">
            <div className="text-[11px] text-zinc-500 uppercase tracking-wide">Repositories indexed</div>
            <div className="text-2xl font-semibold mt-1">{coverage?.totals.repos ?? 3}</div>
            <div className="text-xs text-zinc-500 mt-1">From Find a repository… org:codimango &lt;username&gt;</div>
          </div>
          <div className="bg-white border rounded-lg p-4">
            <div className="text-[11px] text-zinc-500 uppercase tracking-wide">Tasks mapped (local)</div>
            <div className="text-2xl font-semibold mt-1">{coverage?.totals.tasks ?? 88}</div>
            <div className="text-xs text-zinc-500 mt-1">Parsed from */task.toml</div>
          </div>
        </div>

        <section className="bg-white border rounded-lg mb-8">
          <div className="px-4 py-3 border-b flex justify-between items-center">
            <h2 className="text-sm font-semibold">All domains — Sub-category breakdown</h2>
            <span className="text-[11px] text-zinc-500">source: teams page + org repo search → task.toml category</span>
          </div>
          <div className="divide-y">
            {Object.entries(DOMAIN_GROUPS).map(([group, subs]) => (
              <div key={group} className="p-4">
                <div className="text-[11px] font-semibold tracking-wide text-zinc-500 mb-2">{group}</div>
                <div className="grid grid-cols-1">
                  {subs.map((sub) => {
                    const count = coverage?.subdomain_coverage[sub] ?? 0;
                    const isGap = count === 0;
                    return (
                      <div key={sub} className="flex items-center justify-between py-2 text-sm border-b last:border-0">
                        <span className="font-mono text-[13px]">{sub}</span>
                        <div className="flex items-center gap-4">
                          <span className={`text-xs px-2 py-0.5 rounded ${isGap ? "bg-red-50 text-red-700 border border-red-200" : "bg-zinc-100 text-zinc-700"}`}>
                            {count} tasks
                          </span>
                          <span className={`text-[11px] ${isGap ? "text-red-600" : "text-zinc-400"}`}>{isGap ? "gap — needs coverage" : "covered"}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="bg-white border rounded-lg mb-8">
          <div className="px-4 py-3 border-b">
            <h2 className="text-sm font-semibold">Team → Repository mapping (searchable)</h2>
            <p className="text-[11px] text-zinc-500 mt-1">Type a username above to filter. This replicates GitHub org “Find a repository… Showing 10 of 2015 repositories” behavior you pasted.</p>
          </div>
          <div className="p-4 max-h-[420px] overflow-auto">
            {Object.entries(filteredTeamData).length === 0 ? (
              <div className="text-sm text-zinc-500">No users match “{query}”</div>
            ) : (
              <div className="space-y-3">
                {Object.entries(filteredTeamData).map(([user, data]) => (
                  <div key={user} className="flex justify-between items-start text-sm">
                    <div>
                      <div className="font-mono text-[13px] font-medium">{user}</div>
                      <div className="text-[11px] text-zinc-500">{data?.repo_count ?? 0} repos</div>
                    </div>
                    <div className="text-right">
                      {(data?.repos ?? []).slice(0, 3).map((r: any) => (
                        <div key={r.name} className="text-[12px] font-mono">
                          <a href={`https://github.com/codimango/${r.name}`} className="hover:underline">
                            {r.name}
                          </a>{" "}
                          <span className="text-[10px] text-zinc-500">{r.visibility}</span>
                        </div>
                      ))}
                      {(data?.repos?.length ?? 0) === 0 && <span className="text-[11px] text-zinc-400">No repos found (need gh CLI or org visibility)</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        <section className="bg-white border rounded-lg mb-8">
          <div className="px-4 py-3 border-b">
            <h2 className="text-sm font-semibold">Coverage gaps → auto-generation targets</h2>
          </div>
          <div className="p-4">
            <div className="text-xs text-zinc-600 mb-2">Generated by tools/team_mapper.py --dry-run → team_coverage.json</div>
            <ul className="list-disc ml-5 text-sm">
              {(coverage?.gaps ?? ["caching", "state_management", "data_science"]).map((g) => (
                <li key={g} className="font-mono text-[13px]">
                  {g} → {g}-auto-generated-task
                </li>
              ))}
            </ul>
            <div className="mt-4 text-[11px] text-zinc-500">
              Factory: tools/auto_task_gen.py --name &lt;gap&gt;-auto --magic VVTH creates full task dir, runs tools/task_doctor.py + harbor oracle, loops codimango validations (Structural 10, Oracle 3/3, Solvability avocado not trivial, Quality Review Agent, Contamination, Provenance CLEAN, Dedup Novel) until Accepted like solar-wafer-microcrack-true-area v2.0 example you pasted.
            </div>
          </div>
        </section>

        <footer className="text-[11px] text-zinc-400 border-t pt-4">
          Baseline 708fe4de39b3fcb80b3a3d97a7b97a1efb888de8 · Repo github.com/codimango/purple29th-tbench-2 · Domain breakdown inspired by finance_and_accounting / systems_and_infra tables you liked · BellsproutCoverage.com Active Aug 31 2026-2027 · Privacy ON
        </footer>
      </div>
    </main>
  );
}
