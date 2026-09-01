/**
 * Health check — required by Nest / Tupperware FaaS
 * Must return 200 quickly. Used by `nest build --push` verification and curl --cert check.
 */
export async function GET() {
  return Response.json({ status: 'healthy', app: 'bellsproutcoverage', infra: 'nest:x2p:tupperware', ts: Date.now() });
}
