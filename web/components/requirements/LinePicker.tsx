"use client";
// Add a requirement the agent missed by selecting its lines on the main RFP page (P-15): click the first line,
// shift-click the last, or type the line numbers. The quote stored is those lines verbatim, so its source is exact.
// Page headers and footers in the range are left out, as the reader leaves them out.  Owner: Piyush.
import { useEffect, useMemo, useState } from "react";
import { Alert, Busy, Skeleton } from "@/components/ui";
import { api, errorMessage as message, post, useApi } from "@/lib/api";
import type { Doc, Requirement } from "@/lib/types";

const MAX_LINES = 40; // as the API (requirements.service.MAX_SELECTED_LINES)

interface Line { n: number; text: string; bbox: number[]; furniture?: boolean }
interface LayoutPage { page: number; width: number; height: number; unreviewed: boolean; lines: Line[] }

export default function LinePicker({ oppId, startPage, categories, requirements, onAdded }: {
  oppId: string; startPage: number; categories: string[];
  requirements: Requirement[]; // active ones: their lines are shown as already captured
  onAdded: () => unknown;
}) {
  const { data: opp, error: oppError } = useApi<{ documents: Doc[] }>(`/api/opportunities/${oppId}`);
  const doc = opp?.documents.find((d) => d.role === "main");
  const docId = doc?.status === "ingested" ? doc.id : undefined;
  const pageCount = doc?.page_count ?? 1;
  const [wanted, setPageNo] = useState(startPage);
  const pageNo = Math.min(Math.max(1, wanted), pageCount);
  const [loaded, setLoaded] = useState<{ key: string; page?: LayoutPage; error?: string }>();
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [pivot, setPivot] = useState<number>(); // the line a shift-click extends from
  const [text, setText] = useState("");
  const [category, setCategory] = useState(categories[0]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const [added, setAdded] = useState<string>();

  const key = `${docId}/${pageNo}`;
  useEffect(() => {
    if (!docId) return;
    let live = true;
    api<LayoutPage>(`/api/documents/${docId}/pages/${pageNo}`).then(
      (page) => { if (live) setLoaded({ key: `${docId}/${pageNo}`, page }); },
      (e) => { if (live) setLoaded({ key: `${docId}/${pageNo}`, error: message(e) }); });
    return () => { live = false; };
  }, [docId, pageNo]);
  const page = loaded?.key === key ? loaded.page : undefined;

  const covered = useMemo(() => {
    const s = new Set<number>();
    for (const r of requirements)
      if (r.document_id === docId && r.page === pageNo && r.line_start && r.line_end)
        for (let n = r.line_start; n <= r.line_end; n++) s.add(n);
    return s;
  }, [requirements, docId, pageNo]);

  if (oppError) return <Alert kind="error">{oppError}</Alert>;
  if (!opp) return <Skeleton lines={3} />;
  if (!docId) return <Alert kind="info">Upload the main RFP and wait until it has been read.</Alert>;

  const last = page ? Math.max(0, ...page.lines.map((l) => l.n)) : 0;
  const a = Number.parseInt(from, 10);
  const b = Number.parseInt(to || from, 10);
  const inRange = (n: number) => a >= 1 && b >= a && n >= a && n <= b;
  const body = (page?.lines ?? []).filter((l) => inRange(l.n) && !l.furniture && l.text.trim());
  const quote = body.map((l) => l.text).join(" ");
  const problem = !from || !page ? ""
    : !(a >= 1 && b >= 1) ? "Line numbers start at 1."
    : b < a ? "The first line must come before the last line."
    : b > last ? `Page ${pageNo} has ${last} lines.`
    : b - a + 1 > MAX_LINES ? `Select at most ${MAX_LINES} lines; split a longer passage into several requirements.`
    : !body.length ? "Only header or footer lines are selected; select the requirement's own lines." : "";

  const clear = () => { setFrom(""); setTo(""); setPivot(undefined); setError(undefined); };
  const goTo = (n: number) => { setPageNo(Math.min(pageCount, Math.max(1, n || 1))); clear(); setAdded(undefined); };
  const pick = (n: number, extend: boolean) => {
    setError(undefined); setAdded(undefined);
    if (extend && pivot !== undefined) { setFrom(String(Math.min(pivot, n))); setTo(String(Math.max(pivot, n))); }
    else { setFrom(String(n)); setTo(String(n)); setPivot(n); }
  };

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (busy || !quote || problem) return;
    setBusy(true); setError(undefined); setAdded(undefined);
    try {
      const req = await post<Requirement>(`/api/opportunities/${oppId}/requirements/from-lines`,
        { page: pageNo, line_start: a, line_end: b, text, category });
      clear(); setText("");
      setAdded(`${req.req_id} added (${req.source}); it is in the list, to review like the others.`);
      await onAdded();
    } catch (err) { setError(message(err)); } finally { setBusy(false); }
  }

  return (
    <div className="lp">
      <div className="lp-viewer">
        <div className="pager">
          <button type="button" aria-label="Previous page" disabled={pageNo <= 1} onClick={() => goTo(pageNo - 1)}>◀</button>
          <span>Page <input type="number" aria-label="RFP page number" min={1} max={pageCount} value={pageNo}
            onChange={(e) => goTo(Number(e.target.value))} /> / {pageCount}</span>
          <button type="button" aria-label="Next page" disabled={pageNo >= pageCount} onClick={() => goTo(pageNo + 1)}>▶</button>
          {page?.unreviewed && <span className="warn" role="status">No text layer: this page was not read (needs OCR)</span>}
          {!page && loaded?.key !== key && <Busy label="Loading the page lines…" />}
        </div>
        <div className="page lp-page">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={`/api/documents/${docId}/pages/${pageNo}.png`} alt={`RFP page ${pageNo}`} draggable={false} />
          {/* Mouse selection; the line-number fields beside the page are the keyboard way to select. */}
          {page && page.lines.map((l) => {
            const [x0, y0, x1, y1] = l.bbox;
            return (
              <div key={l.n} aria-hidden="true" onClick={(e) => pick(l.n, e.shiftKey)}
                title={`Line ${l.n}${l.furniture ? " (header or footer: left out of the quote)" : ""}: ${l.text}`}
                className={`lp-line${inRange(l.n) ? " on" : ""}${covered.has(l.n) ? " covered" : ""}${l.furniture ? " furniture" : ""}`}
                style={{ left: `${(x0 / page.width) * 100}%`, top: `${(y0 / page.height) * 100}%`,
                  width: `${((x1 - x0) / page.width) * 100}%`, height: `${((y1 - y0) / page.height) * 100}%` }} />
            );
          })}
        </div>
        {!page && loaded?.key === key && loaded.error && <Alert kind="error">{loaded.error}</Alert>}
        <p className="muted lp-legend"><span><i className="lp-swatch covered" /> already a requirement</span>
          <span><i className="lp-swatch on" /> selected</span> <span><i className="lp-swatch furniture" /> header or footer (left out)</span></p>
      </div>

      <form className="form compact lp-side" onSubmit={submit} aria-label="Add a requirement from selected lines">
        <p className="muted">Click the first line of the requirement on the page, then shift-click its last line. Or type the line numbers.</p>
        <div className="lp-range">
          <label>From line <input type="number" className="narrow" min={1} max={last || undefined} value={from}
            onChange={(e) => { setFrom(e.target.value); setPivot(Number.parseInt(e.target.value, 10) || undefined); setAdded(undefined); }} /></label>
          <label>To line <input type="number" className="narrow" min={1} max={last || undefined} value={to} placeholder={from}
            onChange={(e) => { setTo(e.target.value); setAdded(undefined); }} /></label>
          {from && <button type="button" className="secondary" onClick={clear}>Clear</button>}
        </div>
        <div aria-live="polite">
          {problem ? <p className="warn">{problem}</p>
            : quote ? (<>
              <div className="muted">Quote that will be stored (p. {pageNo}, {a === b ? `line ${a}` : `lines ${a}-${b}`})</div>
              <blockquote className="lp-quote">{quote}</blockquote>
            </>) : <p className="muted">No lines selected.</p>}
        </div>
        <label>Short text (optional; default: the quote) <input value={text} maxLength={200} onChange={(e) => setText(e.target.value)} /></label>
        <label>Category <select value={category} onChange={(e) => setCategory(e.target.value)}>
          {categories.map((c) => <option key={c}>{c}</option>)}</select></label>
        <span className="inline"><button disabled={busy || !quote || !!problem}>{busy ? "Adding…" : "Add requirement"}</button></span>
        <Alert kind="error" onClose={() => setError(undefined)}>{error}</Alert>
        <Alert kind="success" onClose={() => setAdded(undefined)}>{added}</Alert>
      </form>
    </div>
  );
}
