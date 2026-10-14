"use client";
// The RFP page behind a matrix row, with the requirement's lines highlighted.  Owner: Janvia.
// Same page-coordinate conversion as the Traceability page: a box [x0, y0, x1, y1] is in the page's own units, so each edge
// is a share of the page's width and height from GET /api/documents/{id}/pages/{n}. A quote across a page break has several
// spans: one button per page. No coordinates stored means no boxes are drawn, only an explanation.
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { Alert, Busy } from "@/components/ui";
import type { MatrixRow } from "./types";

type Size = { width: number; height: number };

function PageView({ docId, pageNo, boxes, label }: { docId: string; pageNo: number; boxes: number[][]; label: string }) {
  const [image, setImage] = useState<"loading" | "ready" | "error">("loading");
  const [size, setSize] = useState<Size | "error">();
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let live = true;
    api<Size>(`/api/documents/${docId}/pages/${pageNo}`).then((p) => { if (live) setSize({ width: p.width, height: p.height }); }, () => { if (live) setSize("error"); });
    return () => { live = false; };
  }, [docId, pageNo]);
  const drawable = image === "ready" && size && size !== "error" && size.width > 0 && size.height > 0;
  return (
    <div className="preview-page">
      {image === "loading" && <Busy label="Loading the page…" />}
      {image === "error" && (
        <Alert kind="error">The page image could not be loaded.{" "}
          <button type="button" className="link" onClick={() => { setImage("loading"); setAttempt(attempt + 1); }}>Try again</button></Alert>
      )}
      <div className="page" hidden={image === "error"}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img key={attempt} src={`/api/documents/${docId}/pages/${pageNo}.png${attempt ? `?retry=${attempt}` : ""}`} alt={`${label}, with the source lines highlighted`}
          onLoad={() => setImage("ready")} onError={() => setImage("error")} />
        {drawable && boxes.map(([x0, y0, x1, y1], i) => (
          <div key={i} className="hl sel" aria-hidden="true" data-testid="source-highlight"
            style={{ left: `${(x0 / size.width) * 100}%`, top: `${(y0 / size.height) * 100}%`,
              width: `${((x1 - x0) / size.width) * 100}%`, height: `${((y1 - y0) / size.height) * 100}%` }} />
        ))}
      </div>
      {image === "ready" && size === "error" && <p className="muted">Highlights are unavailable: the page size could not be read.</p>}
      {image === "ready" && size && size !== "error" && boxes.length === 0 && <p className="muted">No highlight boxes are stored for this page; only the page is shown.</p>}
    </div>
  );
}

/** Lines as the page reference reads them: neighbouring or overlapping lines become one range ("22-26"). */
function lineRanges(spans: [number, number][]): string[] {
  const merged: [number, number][] = [];
  for (const [a, b] of [...spans].sort((x, y) => x[0] - y[0])) {
    const last = merged[merged.length - 1];
    if (last && a <= last[1] + 1) last[1] = Math.max(last[1], b); else merged.push([a, b]);
  }
  return merged.map(([a, b]) => (a === b ? `${a}` : `${a}-${b}`));
}

export default function SourcePreview({ row, docName, traceHref }: { row: MatrixRow; docName: string; traceHref: string }) {
  // One entry per page the source touches, in order; the boxes of every span on that page.
  const pages = useMemo(() => {
    const out: { docId: string; page: number; boxes: number[][]; spans: [number, number][] }[] = [];
    for (const s of row.spans) {
      if (!s.document_id || !s.page) continue;
      let p = out.find((x) => x.docId === s.document_id && x.page === s.page);
      if (!p) { p = { docId: s.document_id, page: s.page, boxes: [], spans: [] }; out.push(p); }
      p.boxes.push(...s.bboxes);
      if (s.line_start) p.spans.push([s.line_start, s.line_end ?? s.line_start]);
    }
    return out.map(({ spans, ...p }) => ({ ...p, lines: lineRanges(spans) }));
  }, [row.spans]);
  const [idx, setIdx] = useState(0);
  if (pages.length === 0) {
    return <p className="preview-empty">No source location is stored for this requirement, so there is no page to show and nothing to highlight.{" "}
      <Link href={traceHref}>Open in Traceability</Link></p>;
  }
  const p = pages[Math.min(idx, pages.length - 1)];
  const lines = p.lines.length ? `, line${p.lines.length > 1 || p.lines[0].includes("-") ? "s" : ""} ${p.lines.join(", ")}` : "";
  return (
    <div className="preview" data-tour="matrix-source-preview">
      <p className="preview-ref"><strong>{docName}, page {p.page}{lines}</strong></p>
      {pages.length > 1 && (
        <div className="preview-pages" role="group" aria-label="Pages of this source">
          {pages.map((x, i) => <button key={`${x.docId}/${x.page}`} type="button" className="chip" aria-pressed={i === idx} onClick={() => setIdx(i)}>Page {x.page}</button>)}
        </div>
      )}
      <PageView key={`${p.docId}/${p.page}`} docId={p.docId} pageNo={p.page} boxes={p.boxes} label={`${docName}, page ${p.page}`} />
      <p><Link href={traceHref}>Open in Traceability</Link></p>
    </div>
  );
}
