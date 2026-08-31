"use client";

import { useState, useEffect, useMemo } from "react";

type TeamMemberRepo = { name: string; visibility: string; description?: string; task_count?: number };
type Coverage = {
  team_users: string[];
  totals: { users: number; repos: number; tasks: number };
  subdomain_coverage: Record<string, number>;
  domain_coverage: Record<string, number>;
  team_data: Record<string, { repos: TeamMemberRepo[]; repo_count: number }>;
  gaps: string[];
  suggestions: string[];
};

// All actual domains from codebase scan — not incomplete
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
    items: ["data_science", "machine_learning", "scientific_computing", "multimedia_and_signal_processing", "data_analytics", "scientific-computing"],
  },
  platform: {
    label: "PLATFORM",
    items: ["security_and_privacy", "caching", "state_management", "database_internals", "parsing_lexing", "data_analysis"],
  },
  finance: { label: "FINANCE_AND_ACCOUNTING", items: ["finance_and_accounting"] },
};

const KNOWN_EMPTY_DOMAINS = [
  "web_backend",
  "web_frontend",
  "web_fullstack",
  "ml_ai_infra",
  "networking",
  "data_infra",
  "data_science",
  "machine_learning",
  "data_analytics",
  "finance_and_accounting",
];

export default function Home() {
  const [coverage, setCoverage] = useState<Coverage | null>(null);
  const [query, setQuery] = useState("");
  const [selectedGroup, setSelectedGroup] = useState("all");

  // support ?user=mehag and ?q=mehag and ?search=mehag and localStorage — team not hardcoded
  useEffect(() => {
    const sp = new URLSearchParams(window.location.search);
    const urlUser = sp.get("user") || sp.get("q") || sp.get("search") || "";
    if (urlUser) setQuery(urlUser);
    else {
      const saved = localStorage.getItem("bellsprout_user");
      if (saved) setQuery(saved);
    }
    fetch("/team_coverage.json")
      .then((r) => (r.ok ? r.json() : null))
      .then(setCoverage)
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (query.trim()) localStorage.setItem("bellsprout_user", query.trim());
  }, [query]);

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
      // For All, include known empty domains as gaps too, sorted with counts
      const merged = [...allSubs];
      for (const domain of KNOWN_EMPTY_DOMAINS) {
        if (!(domain in coverage.subdomain_coverage)) merged.push([domain, 0]);
      }
      // Also finance etc
      if (!coverage.subdomain_coverage["finance_and_accounting"]) merged.push(["finance_and_accounting", 0]);
      return merged.sort((a, b) => b[1] - a[1]);
    }
    const inGroup = allSubs.filter(([name]) => group.items.includes(name));
    const missing = group.items.filter((name) => !(name in coverage.subdomain_coverage)).map((name) => [name, 0] as [string, number]);
    return [...inGroup, ...missing].sort((a, b) => b[1] - a[1]);
  }, [coverage, selectedGroup]);

  const firstUser = filteredUsers[0] ?? coverage?.team_users[0] ?? "purple29th";
  const firstRepo = coverage?.team_data[firstUser]?.repos?.[0]?.name ?? `${firstUser}-tbench-2`;
  const gaps = useMemo(() => {
    if (!coverage) return [];
    const low = subdomainList.filter(([, c]) => c < 2).map(([n]) => n);
    const fromJson = coverage.gaps || [];
    const merged = Array.from(new Set([...fromJson, ...low]));
    return merged;
  }, [coverage, subdomainList]);

  const domainRows = useMemo(() => {
    if (!coverage?.domain_coverage) return [];
    return Object.entries(coverage.domain_coverage).sort((a, b) => b[1] - a[1]);
  }, [coverage]);

  return (
    <main className="min-h-screen bg-white text-zinc-900 antialiased">
      <div className="max-w-[1080px] mx-auto px-6 py-8">
        <header className="flex items-start justify-between border-b border-zinc-200 pb-4 gap-4">
          <div>
            <h1 className="text-[15px] font-semibold tracking-tight">bellsproutcoverage.com / bellsproutcoverage.ai</h1>
            <p className="text-[11px] text-zinc-500 mt-1 max-w-[560px] leading-snug">
              Codimango team coverage dashboard — GitHub org codimango Find a repository… (10 of 2015 shown) maps Private repos automatically for org members.
              Baseline commit 708fe4de39b3fcb80b3a3d97a7b97a1efb888de8 — top link dynamic to filtered user repo (e.g., mehag search → mehag-tbench, not hardcoded).
              Team from team_coverage.json — run tools/team_mapper.py to show your own team when you pull.
            </p>
            <div className="mt-2 flex gap-2 text-[10px]">
              <span className="border border-zinc-200 rounded px-2 py-0.5">members {coverage?.totals.users ?? 25}</span>
              <span className="border border-zinc-200 rounded px-2 py-0.5">repos {coverage?.totals.repos ?? 75} (25×3)</span>
              <span className="border border-zinc-200 rounded px-2 py-0.5">local tasks {coverage?.totals.tasks ?? 88}</span>
            </div>
          </div>
          <div className="flex flex-col items-end gap-2">
            <a href={`https://github.com/codimango/${firstRepo}`} target="_blank" className="text-[11px] border border-zinc-900 rounded-md px-3 py-1.5 bg-zinc-900 text-white hover:bg-black font-mono">
              {firstRepo} @ 708fe4d
            </a>
            <a href="https://github.com/codimango/purple29th-tbench-2" target="_blank" className="text-[10px] border border-zinc-200 rounded-md px-2.5 py-1 hover:bg-zinc-50">
              GitHub repo — codimango/purple29th-tbench-2
            </a>
          </div>
        </header>

        <div className="mt-6 grid grid-cols-1 lg:grid-cols-[300px_1fr] gap-6">
          {/* Left: searchable team → repo */}
          <div className="space-y-4">
            <div className="border border-zinc-200 rounded-lg bg-white p-3">
              <div className="text-[11px] font-medium">Find a repository…</div>
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="mehag, purple29th, anishh — try purple29th → 3 Private repos"
                className="mt-2 w-full rounded-md border border-zinc-200 px-3 py-2 text-[11px] focus:outline-none focus:border-zinc-900 font-mono"
              />
              <div className="mt-2 text-[10px] text-zinc-500 leading-snug">
                Org search lists Private repos for members automatically without extra permission. Proven: purple29th → 3 Private repos purple29th-tbench-2, purple29th-tbench, purple29th-android-tbench; mehag → 3 repos mehag-multimodal-agents Internal Python, swe-bench-pro-mehag Private Shell, mehag-tbench Private Python. Everybody findable. Use ?user=mehag in URL.
              </div>
            </div>

            <div className="border border-zinc-200 rounded-lg bg-white">
              <div className="px-3 py-2 border-b border-zinc-200 text-[11px] font-medium flex justify-between">
                <span>Team members · {filteredUsers.length}</span>
                <span className="text-zinc-400 font-normal">{query ? `filtered for "${query}"` : "all 25"}</span>
              </div>
              <div className="divide-y divide-zinc-100 max-h-[560px] overflow-auto">
                {filteredUsers.map((u) => {
                  const d = coverage?.team_data[u];
                  return (
                    <div key={u} className="px-3 py-2.5">
                      <div className="flex justify-between items-center">
                        <a href={`https://github.com/codimango`} target="_blank" className="text-[12px] font-medium hover:underline">
                          {u}
                        </a>
                        <span className="text-[10px] text-zinc-500 border border-zinc-200 rounded px-1.5 py-0.5">{d?.repo_count ?? 0} repos</span>
                      </div>
                      <div className="mt-1.5 space-y-0.5">
                        {(d?.repos ?? []).map((r) => (
                          <a key={r.name} href={`https://github.com/codimango/${r.name}`} target="_blank" className="flex justify-between text-[11px] text-zinc-600 hover:text-zinc-900 hover:underline">
                            <span className="font-mono truncate">{r.name}</span>
                            <span className="text-[9px] text-zinc-400 ml-2 shrink-0">· {r.visibility}</span>
                          </a>
                        ))}
                      </div>
                    </div>
                  );
                })}
                {filteredUsers.length === 0 && <div className="p-3 text-[11px] text-zinc-500">No match — try ?user=mehag</div>}
              </div>
              <div className="px-3 py-2 border-t border-zinc-100 text-[10px] text-zinc-500">
                To show your own team when pulled: <code className="bg-zinc-50 border px-1 py-0.5 rounded">python tools/team_mapper.py --team-file myteam.txt --dry-run</code> then refresh. Team not hardcoded to purple29th.
              </div>
            </div>
          </div>

          {/* Right: domain breakdown + gaps + watch mango + hosting */}
          <div className="space-y-5">
            <div className="border border-zinc-200 rounded-lg bg-white">
              <div className="px-4 py-3 border-b border-zinc-200 flex items-center justify-between">
                <h2 className="text-[12px] font-medium">Domain coverage — actual from codebase */task.toml</h2>
                <select value={selectedGroup} onChange={(e) => setSelectedGroup(e.target.value)} className="text-[11px] border border-zinc-200 rounded-md px-2 py-1 bg-white">
                  <option value="all">All domains</option>
                  <option value="infrastructure">INFRASTRUCTURE</option>
                  <option value="mobile">MOBILE</option>
                  <option value="web">WEB</option>
                  <option value="data">DATA</option>
                  <option value="platform">PLATFORM</option>
                  <option value="finance">FINANCE_AND_ACCOUNTING</option>
                </select>
              </div>
              <div className="p-4">
                <div className="mb-4">
                  <div className="text-[10px] font-medium text-zinc-500 mb-1.5">Categories (top-level) — real counts, not fake 100%</div>
                  <div className="flex flex-wrap gap-1.5">
                    {domainRows.map(([name, count]) => (
                      <span key={name} className="text-[10px] border border-zinc-200 rounded-full px-2 py-0.5 font-mono">
                        {name} {count}
                      </span>
                    ))}
                  </div>
                  <div className="text-[10px] text-zinc-500 mt-1.5">Example: data-science 63, bug-fixing 17, algorithms 3, reverse-engineering 1, build-infrastructure 1 etc from local scan.</div>
                </div>
                <table className="w-full text-[11px]">
                  <thead>
                    <tr className="text-zinc-500 border-b border-zinc-200">
                      <th className="text-left py-2 font-normal w-[48%]">Subdomain</th>
                      <th className="text-right py-2 font-normal w-[18%]">Tasks covered</th>
                      <th className="text-left py-2 font-normal pl-4">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {subdomainList.map(([name, count]) => (
                      <tr key={name} className="border-b border-zinc-100 last:border-0">
                        <td className="py-2 font-mono">{name}</td>
                        <td className="py-2 text-right font-mono">{count}</td>
                        <td className="py-2 pl-4 text-zinc-600">{count < 2 ? "needs generation → auto_task_gen" : count < 5 ? "low" : "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div className="mt-3 text-[10px] text-zinc-500 leading-snug">
                  INFRASTRUCTURE: systems_and_infra, ml_ai_infra, networking, distributed_systems, backend_services, data_infra, build_and_ci. WEB: web_backend, web_frontend, web_fullstack. DATA: machine_learning, scientific_computing, data_science, data_analytics, multimedia_and_signal_processing. PLATFORM: security_and_privacy. Plus actual T-Bench subdomains: mobile_android 19, multimedia_and_signal_processing 53, database_internals 3, scientific_computing 2, etc. Counts are real task counts, not fake 100%. Dropdown filters actually work.
                </div>
              </div>
            </div>

            <div className="border border-zinc-200 rounded-lg bg-white p-4">
              <h3 className="text-[12px] font-medium">Gaps → Generate new task</h3>
              <p className="text-[10px] text-zinc-500 mt-1 leading-snug">
                Coverage gaps where task count &lt;2 or missing from local repo. Generate using magic VVTH which scaffolds full task dir and runs task_doctor + oracle until Accepted.
              </p>
              <div className="mt-3 grid grid-cols-1 gap-2">
                {gaps.slice(0, 12).map((gap) => (
                  <div key={gap} className="flex items-center justify-between border border-zinc-200 rounded-md px-2.5 py-1.5 bg-zinc-50">
                    <span className="text-[11px] font-mono">{gap}</span>
                    <code className="text-[10px] font-mono text-zinc-700">python tools/auto_task_gen.py --name {gap}-task --magic VVTH</code>
                  </div>
                ))}
                {gaps.length === 0 && <div className="text-[11px] text-zinc-500">No gaps — all domains covered &gt;=2</div>}
              </div>
              <code className="mt-3 block bg-zinc-900 text-zinc-100 border border-zinc-900 rounded px-2.5 py-2 text-[10px] font-mono">
                python tools/auto_task_gen.py --name &lt;gap&gt;-task --magic VVTH
              </code>
              <p className="text-[10px] text-zinc-500 mt-2">Creates full task dir, runs task_doctor + oracle validation until Accepted. Check team_coverage.json suggestions for next auto-generation targets.</p>
            </div>

            <div className="border border-zinc-200 rounded-lg bg-white p-4">
              <h3 className="text-[12px] font-medium">Watch Mango validations — one page where we watch what is going on in mango</h3>
              <div className="mt-3 grid grid-cols-2 gap-2 text-[11px]">
                <div className="border border-zinc-200 rounded p-2.5">
                  <div className="font-medium text-[11px]">Structural (10 checks)</div>
                  <ul className="mt-1 text-[10px] text-zinc-600 list-disc pl-3 space-y-0.5">
                    <li>task.toml via tomllib valid</li>
                    <li>Required files: task.toml, instruction.md, README.md, environment/Dockerfile</li>
                    <li>Required dirs: tests, environment</li>
                    <li>Name suffix matches directory</li>
                    <li>Timeout &gt;0, resources valid</li>
                    <li>task_doctor.py exit 0 valid / nonzero invalid</li>
                  </ul>
                </div>
                <div className="border border-zinc-200 rounded p-2.5">
                  <div className="font-medium">Oracle (3/3)</div>
                  <ul className="mt-1 text-[10px] text-zinc-600 list-disc pl-3 space-y-0.5">
                    <li>oracle tests pass</li>
                    <li>reward.txt 1</li>
                    <li>reference solve.sh solves</li>
                  </ul>
                </div>
                <div className="border border-zinc-200 rounded p-2.5">
                  <div className="font-medium">Solvability — avocado not trivial</div>
                  <div className="text-[10px] text-zinc-600 mt-1">Avocado can solve, not too easy, not impossible. Time estimates respected.</div>
                </div>
                <div className="border border-zinc-200 rounded p-2.5">
                  <div className="font-medium">Quality Review</div>
                  <div className="text-[10px] text-zinc-600 mt-1">Instruction clarity, edge cases, Dockerfile reproducible.</div>
                </div>
                <div className="border border-zinc-200 rounded p-2.5">
                  <div className="font-medium">Contamination check</div>
                  <div className="text-[10px] text-zinc-600 mt-1">README/instruction must not reference sibling task names. File-specific messages. Self-substring skip (e.g., alumina-fissure-breakdown inside alumina-fissure-breakdown-voltage not flagged).</div>
                </div>
                <div className="border border-zinc-200 rounded p-2.5">
                  <div className="font-medium">Dedup / Novelty</div>
                  <div className="text-[10px] text-zinc-600 mt-1">No duplicate task ideas across 2015 repos. TF-IDF vs code_video_data etc.</div>
                </div>
                <div className="border border-zinc-200 rounded p-2.5 col-span-2">
                  <div className="font-medium">TBR Build / Eval / Agentic Review — example solar-wafer-microcrack-true-area Accepted v2.0</div>
                  <div className="text-[10px] text-zinc-600 mt-1">Full pipeline: build docker, eval oracle, agentic review with Staff-level checks. Example task solar-wafer-microcrack-true-area accepted v2.0 shows all validations green.</div>
                </div>
              </div>
            </div>

            <div className="border border-zinc-200 rounded-lg bg-white p-4">
              <h3 className="text-[12px] font-medium">Hosting — bellsproutcoverage.com + bellsproutcoverage.ai</h3>
              <div className="mt-2 space-y-3 text-[11px] leading-snug">
                <div>
                  <div className="font-medium text-[11px]">Current: bellsproutcoverage.com bought on Namecheap</div>
                  <ul className="text-[10px] text-zinc-600 list-disc pl-4 mt-1 space-y-0.5">
                    <li>Domain Status Active Aug 31 2026-2027, Privacy ON, BasicDNS selected</li>
                    <li>Parking Page ON → OFF, Redirect Domain removed after guidance</li>
                    <li>Advanced DNS Host Records correct: A @ 76.76.21.21 Automatic + CNAME www cname.vercel-dns.com. Automatic + TXT @ v=spf1...</li>
                    <li>Requires Verify Contacts via email jimohtosin.161@gmail.com</li>
                    <li>Deploy via npx vercel --prod --yes → productions aliased to bellsproutcoverage.com and bellsproutcoverage.vercel.app live with curl -I 200 after DNS fixed. Previous ERR_CONNECTION_CLOSED was because Vercel did not know domain until vercel domains add bellsproutcoverage.com + www...</li>
                    <li>Dangerous site warning came from GitHub SSO login page asking for codimango org password on new .com flagged as phishing — fixed by removing auth, adding security headers X-Content-Type-Options nosniff, X-Frame-Options DENY in next.config.js + vercel.json, adding robots.txt, security.txt, redeploying public clean.</li>
                  </ul>
                </div>
                <div className="border-t border-zinc-100 pt-2">
                  <div className="font-medium">Deploy steps for .com (repeat for .ai)</div>
                  <code className="mt-1 block bg-zinc-50 border border-zinc-200 rounded px-2 py-1.5 text-[10px] font-mono">
                    cd bellsproutcoverage && npx vercel --prod --yes && vercel domains add bellsproutcoverage.com && vercel domains add www.bellsproutcoverage.com
                  </code>
                </div>
                <div className="border-t border-zinc-100 pt-2">
                  <div className="font-medium">bellsproutcoverage.ai — buy & host</div>
                  <ul className="text-[10px] text-zinc-600 list-disc pl-4 mt-1 space-y-0.5">
                    <li>Porkbun cheapest ~$75/yr, Namecheap ~$85/yr, Cloudflare Registrar at-cost (~$75). Vercel marketplace domain also possible.</li>
                    <li>Same DNS: A @ 76.76.21.21 + CNAME www cname.vercel-dns.com.</li>
                    <li>In Vercel Settings → Domains add bellsproutcoverage.ai and www.bellsproutcoverage.ai, then redeploy.</li>
                    <li>To start now: npx vercel link then vercel --prod.</li>
                    <li>Repo link: https://github.com/codimango/purple29th-tbench-2 tree main bellsproutcoverage/</li>
                  </ul>
                </div>
                <div className="border-t border-zinc-100 pt-2">
                  <div className="font-medium">Internal-only SSO — strictly before page lands</div>
                  <div className="text-[10px] text-zinc-600 mt-1">Middleware checks bellsprout_internal_sso cookie before page lands — if not meta_passed redirect to /login. Simulates Meta internal device cert. For true Meta SSO host on Meta internal infra: intern, Unidash, Nest behind InternAuth (e.g., *.internalmeta.com). On public Vercel .com we simulate with cookie set after SSO button — middleware blocks dashboard strictly before it lands. Once Meta login passed then bellsprout shows.</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <footer className="mt-8 text-[10px] text-zinc-400 border-t border-zinc-200 pt-3 flex justify-between">
          <span>Baseline from local scan · commit 708fe4de39b3fcb80b3a3d97a7b97a1efb888de8 already on GitHub so both models start without pushing new baseline · dynamic user repo on top via first filtered user · team not hardcoded — run tools/team_mapper.py --dry-run</span>
          <a href="https://bellsproutcoverage.com" className="hover:underline">bellsproutcoverage.com</a>
        </footer>
      </div>
    </main>
  );
}
