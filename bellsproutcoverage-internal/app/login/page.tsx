/**
 * Login page — only hit when intern_oauth_token missing.
 * In real Nest, this is handled by OIDC gateway at intern-oidc-gateway.internalmeta.com/login
 * This page is a fallback / logged-out landing that explains device cert requirement.
 */
export default function LoginPage() {
  return (
    <main className="min-h-screen bg-white flex items-center justify-center px-6">
      <div className="max-w-md w-full border border-zinc-200 rounded-lg p-6 bg-white">
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-[10px] font-mono tracking-widest text-zinc-500">INTERNAL · DEVICE CERT REQUIRED</span>
        </div>
        <h1 className="mt-4 text-[18px] font-semibold tracking-tight">bellsproutcoverage.internalmeta.com</h1>
        <p className="mt-2 text-[12px] text-zinc-600 leading-relaxed">
          This dashboard is protected by InternAuth + device certificate (Airlock). Request is blocked at the edge before your code runs if:
        </p>
        <ul className="mt-3 list-disc pl-5 text-[11px] text-zinc-600 space-y-1">
          <li>Not on a Meta-managed device (Secure Enclave/TPM hardware-backed cert missing)</li>
          <li>No valid <code className="font-mono bg-zinc-50 border px-1 rounded">intern_oauth_token</code> (Domain=.internalmeta.com)</li>
          <li>Cert serial not validated via <code className="font-mono bg-zinc-50 border px-1 rounded">ProxygenHTTPHeaders::getValidatedClientCertSerial()</code></li>
        </ul>
        <div className="mt-5 p-3 bg-zinc-50 border border-zinc-200 rounded-md">
          <div className="text-[10px] font-mono text-zinc-500">DEBUG</div>
          <div className="text-[11px] mt-1">Check https://www.internalfb.com/intern/auth/status — must show valid headers. If on OD, use https://&lt;od&gt;-3000--nest-dev-proxy.internalmeta.com (not x2p) to avoid cookie domain loop.</div>
        </div>
        <div className="mt-5 flex gap-2">
          <a href="/" className="text-[11px] bg-zinc-900 text-white rounded-md px-4 py-2 hover:bg-black">Continue to app (OIDC will redirect)</a>
          <a href="https://www.internalfb.com/intern/auth/status" target="_blank" className="text-[11px] border border-zinc-200 rounded-md px-4 py-2 hover:bg-zinc-50">Auth status</a>
        </div>
        <div className="mt-4 text-[10px] text-zinc-400">
          Prev public Vercel attempt used cookie simulation <code>bellsprout_internal_sso=meta_passed</code> + middleware 307 — flagged as phishing (Dangerous site). This Nest version uses real OIDC via @nest/intern-auth.
        </div>
      </div>
    </main>
  );
}
