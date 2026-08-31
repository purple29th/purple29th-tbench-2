"use client";

import { signIn } from "next-auth/react";

export default function LoginPage() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-white">
      <div className="border rounded-lg p-6 max-w-sm w-full">
        <h1 className="text-[14px] font-semibold">bellsproutcoverage.com — Internal only</h1>
        <p className="text-[11px] text-zinc-500 mt-2">
          This dashboard maps your team from codimango teams page to GitHub org Find a repository… (2015 repos). Only internal org members can logon via SSO (GitHub org codimango membership check).
        </p>
        <button onClick={() => signIn("github")} className="mt-4 w-full bg-zinc-900 text-white rounded-md px-3 py-2 text-[12px] hover:bg-black">
          Log in with GitHub SSO (codimango org)
        </button>
        <p className="text-[10px] text-zinc-400 mt-3">Uses GitHub OAuth + org:codimango membership check. If you are not in codimango org, sign-in will be denied.</p>
      </div>
    </main>
  );
}
