// Walkthrough session identity.  Owner: tour engine.
//
// The guided walkthrough must offer itself once per dev-server start: not again after a hot reload (HMR keeps the
// browser page, so React state survives anyway) and not again after a browser refresh. The server process is the
// thing that changes on a restart, so the identity is a random id created once when this module is loaded by the
// server. The launcher fetches it once per page load and compares it with the `session` saved in localStorage
// ("layer0.tour"): a different id means a new server run, so stored progress is reset and the welcome dialog opens;
// the same id means the person already answered (skipped / done) or is in the middle of it (running: resume).
// `force-dynamic` stops Next from caching the response at build time, where the id would be frozen forever.
export const dynamic = "force-dynamic";

// Kept on globalThis: in `next dev` this module can be evaluated again on a later compile (another page is built on
// demand), and a fresh id then would offer the walkthrough again on every newly compiled page.
const g = globalThis as typeof globalThis & { __layer0TourSession?: string };
const SESSION_ID = (g.__layer0TourSession ??= crypto.randomUUID());

export function GET() {
  return Response.json({ id: SESSION_ID }, { headers: { "Cache-Control": "no-store" } });
}
