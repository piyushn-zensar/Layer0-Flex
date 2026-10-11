"use client";
// A change document's page with its change statements highlighted (P-11); the same boxes as Traceability pane 1.  Owner: Piyush.
import type { ChangeItem, ChangeSet } from "@/lib/types";

export default function ChangeDocument({ set, pageNo, onPage, selected, onSelect, tour = false }:
  { set: ChangeSet; pageNo: number; onPage: (n: number) => void; selected?: number; onSelect: (item: ChangeItem) => void; tour?: boolean }) {
  const count = set.pages.length;
  const page = set.pages.find((p) => p.page === pageNo);
  if (!page) return <p className="muted">No page to show.</p>;
  const go = (n: number) => onPage(Math.min(count, Math.max(1, n)));
  const t = (id: string) => (tour ? id : undefined); // walkthrough targets, only on the set the tour points at
  return (
    <>
      <div className="pager" data-tour={t("chg-doc-pager")}>
        <button type="button" aria-label="Previous page" onClick={() => go(pageNo - 1)}>◀</button>
        <span>Page <input type="number" aria-label="Page number" min={1} max={count} value={pageNo} onChange={(e) => go(Number(e.target.value))} /> / {count}</span>
        <button type="button" aria-label="Next page" onClick={() => go(pageNo + 1)}>▶</button>
      </div>
      <div className="page" data-tour={t("chg-doc-page")}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={`/api/documents/${set.document_id}/pages/${pageNo}.png`} alt={`${set.filename}, page ${pageNo}`} />
        {set.items.filter((i) => i.page === pageNo).flatMap((i) => i.bboxes.map(([x0, y0, x1, y1], k) => (
          <div key={`${i.id}-${k}`} title={`Change ${i.n}`} onClick={() => onSelect(i)}
            role="button" tabIndex={k === 0 ? 0 : -1} aria-label={`Select change ${i.n}`}
            onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onSelect(i); } }}
            className={`hl${i.id === selected ? " sel" : ""}`}
            style={{ left: `${(x0 / page.width) * 100}%`, top: `${(y0 / page.height) * 100}%`,
              width: `${((x1 - x0) / page.width) * 100}%`, height: `${((y1 - y0) / page.height) * 100}%` }} />
        )))}
      </div>
    </>
  );
}
