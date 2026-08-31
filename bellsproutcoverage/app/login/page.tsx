"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [checking, setChecking] = useState(false);

  const handleMetaSSO = () => {
    setChecking(true);
    // Simulate Meta internal SSO check — in real Meta infra, this would verify internal device cert + corp network
    // For public .com, we simulate by setting internal SSO cookie that middleware checks strictly before page lands
    // Real implementation would call https://intern-auth or Okta SAML with device posture
    document.cookie = "bellsprout_internal_sso=meta_passed; path=/; max-age=86400; SameSite=Lax";
    setTimeout(() => {
      router.push("/");
    }, 800);
  };

  return (
    <main className="min-h-screen flex items-center justify-center bg-white px-4">
      <div className="w-full max-w-[360px] border border-zinc-200 rounded-lg p-6 bg-white shadow-sm">
        <h1 className="text-[13px] font-semibold">bellsproutcoverage.com — Internal Only</h1>
        <p className="text-[11px] text-zinc-500 mt-2 leading-snug">
          This dashboard maps team coverage from codimango teams to GitHub org Find a repository… (2015 repos). Only internal users can logon. Strictly SSO before page lands — blocked first by internal SSO. You can only continue if using internal device.
        </p>
        <div className="mt-4 border border-zinc-200 rounded-md p-3 bg-zinc-50">
          <div className="text-[10px] font-medium">Meta SSO simulation (public .com cannot use real Meta device cert)</div>
          <div className="text-[10px] text-zinc-500 mt-1">Real Meta SSO for true internal device check requires hosting on Meta internal infra: intern, Unidash, Nest behind InternAuth (e.g., *.internalmeta.com). On public Vercel .com, we simulate with cookie set after SSO button — middleware blocks dashboard strictly before it lands.</div>
        </div>
        <button onClick={handleMetaSSO} disabled={checking} className="mt-4 w-full rounded-md bg-zinc-900 px-3 py-2 text-[11px] font-medium text-white hover:bg-black disabled:opacity-50">
          {checking ? "Checking internal device + Meta SSO…" : "Continue with Meta SSO (internal device required)"}
        </button>
        <div className="mt-3 text-[10px] text-zinc-400">
          GitHub repo: <a href="https://github.com/codimango/purple29th-tbench-2" className="underline">codimango/purple29th-tbench-2</a> — baseline 708fe4d, site code in /bellsproutcoverage, live at bellsproutcoverage.com and bellsproutcoverage.vercel.app
        </div>
      </div>
    </main>
  );
}
