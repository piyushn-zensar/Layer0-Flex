"use client";
// Product details (J-20, C-60, C-63, C-65, C-66): everything the catalog knows about one product, from GET /api/catalog/product.
// A spreadsheet part: its values grouped (input, output, power, mechanical, interfaces and isolation, application), each with its
// source row and import date, "Unknown" for an empty cell, conflicts with the web page shown with both values, its evaluation
// boards (or a board's modules) and its web series. A web listing: what its page publishes, its spreadsheet variants. Both: the
// family's published ratings (spec tables, unverified until the unit confirms them; the family's unit confirms or rejects here),
// documents (opened at the product's pages) and images (placeholder when not verified).  Owner: Janvia (built by Piyush, 23 Oct).
import Link from "next/link";
import { useState } from "react";
import { errorMessage, post, useApi, useMe } from "@/lib/api";
import type { PowerModule, ProductDetail, ProductRow, ProductSpec } from "@/lib/types";
import { Alert, EmptyState, Skeleton, StatusBadge, useToast } from "@/components/ui";
import { fileUrl } from "./ProductThumb";
import { SOURCE_LABEL, TYPE_LABEL } from "./products";

const link = (key: string) => `/catalog/product?part=${encodeURIComponent(key)}`;
type Field = { key: keyof PowerModule; label: string; unit?: string };
const GROUPS: { title: string; fields: Field[] }[] = [
  { title: "Input", fields: [{ key: "vin_min_v", label: "Input voltage, minimum", unit: "V" }, { key: "vin_max_v", label: "Input voltage, maximum", unit: "V" }] },
  { title: "Output", fields: [{ key: "vout_min_v", label: "Output voltage, minimum", unit: "V" }, { key: "vout_max_v", label: "Output voltage, maximum", unit: "V" },
    { key: "vout_typ_v", label: "Output voltage, typical", unit: "V" }, { key: "regulation", label: "Regulation" }, { key: "multi_output", label: "Multiple outputs" }] },
  { title: "Power and current", fields: [{ key: "power_w", label: "Output power", unit: "W" }, { key: "power_peak_w", label: "Output power, peak", unit: "W" },
    { key: "current_a", label: "Output current", unit: "A" }, { key: "current_peak_a", label: "Output current, peak", unit: "A" },
    { key: "efficiency_pct", label: "Typical efficiency", unit: "%" }, { key: "paralleling", label: "Paralleling" }] },
  { title: "Mechanical", fields: [{ key: "length_mm", label: "Length", unit: "mm" }, { key: "width_mm", label: "Width", unit: "mm" }, { key: "height_mm", label: "Height", unit: "mm" },
    { key: "package_type", label: "Package type" }, { key: "footprint", label: "Footprint" }, { key: "mounting", label: "Mounting" }] },
  { title: "Interfaces and isolation", fields: [{ key: "interfaces", label: "Digital interfaces" }, { key: "isolation", label: "Isolation" },
    { key: "isolation_v", label: "Isolation voltage", unit: "V" }, { key: "attributes", label: "Product attributes" }] },
  { title: "Application", fields: [{ key: "application", label: "Applications" }, { key: "product_line", label: "Product line" }, { key: "series", label: "Series" }] },
];

function show(v: unknown, unit?: string): string | null {
  if (v === null || v === undefined || v === "" || (Array.isArray(v) && v.length === 0)) return null;
  if (Array.isArray(v)) return v.join(", ");
  if (typeof v === "boolean") return v ? "Yes" : "No";
  return unit ? `${v} ${unit}` : String(v);
}

function Specs({ d }: { d: ProductDetail }) {
  const conflicts = new Map((d.conflicts ?? []).map((c) => [c.field, c]));
  const row = d.sheet?.row;
  return (
    <div className="spec-groups" data-tour="catalog-detail-specs">
      {GROUPS.map((g) => (
        <section key={g.title} className="card spec-group">
          <h3>{g.title}</h3>
          <dl>{g.fields.map((f) => {
            const value = show(d[f.key], f.unit), c = conflicts.get(f.key as string), when = d.imported?.[f.key as string];
            return (<div key={f.key as string} className="spec-row">
              <dt>{f.label}</dt>
              <dd>{value ?? <span className="muted">Unknown</span>}
                {value && when && <div className="muted spec-src">Spreadsheet{row ? `, row ${row}` : ""}, imported {when}</div>}
                {c && <div className="spec-conflict" role="note"><StatusBadge status="warn" label="Web page disagrees" /> The web page states {c.web} {f.unit ?? ""}
                  {c.web_url && <> (<a href={c.web_url} target="_blank" rel="noopener noreferrer">source</a>)</>}; both values kept for review.</div>}
              </dd></div>);
          })}</dl>
          {g.title === "Output" && (d.outputs?.length ?? 0) > 0 && <><h4>Further outputs</h4><ul className="per-req">{d.outputs!.map((o) => (
            <li key={o.n}>Output {o.n}: {[show(o.v_min, "V min"), show(o.v_nom, "V nominal"), show(o.v_max, "V max"), show(o.power_w, "W"), show(o.current_a, "A")].filter(Boolean).join(", ") || "values unknown"}</li>))}</ul>
            <p className="muted">The configurator checks the main output only.</p></>}
        </section>))}
    </div>
  );
}

const range = (lo: number | null, hi: number | null) => (lo === null && hi === null ? "—" : lo === hi || lo === null || hi === null ? `${lo ?? hi}` : `${lo} to ${hi}`);

function Related({ title, rows, empty }: { title: string; rows: ProductRow[]; empty: string }) {
  return (<section className="card"><h2>{title} ({rows.length})</h2>
    {rows.length === 0 ? <p className="muted">{empty}</p> : <div className="table-scroll"><table className="dense">
      <thead><tr><th>Part number</th><th>Type</th><th className="num">Input (V)</th><th className="num">Output (V)</th><th className="num">Power (W)</th><th className="num">Efficiency (%)</th></tr></thead>
      <tbody>{rows.map((r) => <tr key={r.key}><td><Link className="mono" href={link(r.key)}>{r.part_number}</Link>{r.has_conflict && <> <StatusBadge status="warn" label="Conflict" /></>}</td>
        <td>{TYPE_LABEL[r.product_type]}</td><td className="num">{range(r.vin_min_v, r.vin_max_v)}</td><td className="num">{range(r.vout_min_v, r.vout_max_v)}</td>
        <td className="num">{r.power_w ?? "—"}</td><td className="num">{r.efficiency_pct ?? "—"}</td></tr>)}</tbody></table></div>}
  </section>);
}

function Ratings({ specs, onDone }: { specs: ProductSpec[]; onDone: () => void }) {
  const me = useMe(), toast = useToast();
  const [busy, setBusy] = useState<string>(), [noteFor, setNoteFor] = useState<string>();
  const unitRole = me?.role === "product_manager" || me?.role === "design_engineer";
  const review = (id: string, status: "confirmed" | "rejected", note = "") => {
    setBusy(id);
    post(`/api/catalog/specs/${encodeURIComponent(id)}/review`, { status, note })
      .then(() => { toast.success(status === "confirmed" ? "Ratings confirmed." : "Ratings rejected with your note."); setNoteFor(undefined); onDone(); },
        (e) => toast.error(errorMessage(e))).finally(() => setBusy(undefined));
  };
  return (<section className="card" data-tour="catalog-detail-ratings">
    <h2>Published ratings ({specs.length})</h2>
    <p className="muted">Read from the supplied brochures and the official product pages by a model pass; a value is kept only when its quote is on the
      cited page. Ranges per family or variant, not an orderable configuration. Unverified until the family&apos;s unit confirms them.</p>
    {specs.length === 0 ? <p className="muted">No published ratings were read for this family.</p> : specs.map((s) => (
      <details key={s.spec_id} className="spec-item">
        <summary><strong>{s.variant}</strong> · {s.attributes.length} values · {s.verified ? <StatusBadge status="pass" label="Confirmed by the unit" />
          : s.review?.status === "rejected" ? <StatusBadge status="fail" label="Rejected by the unit" /> : <StatusBadge status="warn" label="Unverified" />}</summary>
        <div className="table-scroll"><table className="dense"><thead><tr><th>Rating</th><th>Value</th><th>Conditions</th><th>Source</th></tr></thead>
          <tbody>{s.attributes.map((a, i) => <tr key={i}><td>{a.label}</td>
            <td>{a.min !== null || a.max !== null ? (a.min !== null && a.max !== null && a.min !== a.max ? `${a.min} to ${a.max}` : `${a.max ?? a.min}`) + ` ${a.unit}` : a.text}</td>
            <td className="muted">{a.conditions || "—"}</td>
            <td><a href={`${fileUrl(a.source.file)}${a.source.file.endsWith(".pdf") ? `#page=${a.page}` : ""}`} target="_blank" rel="noopener noreferrer">
              {a.source.url ? "Product page" : `${a.source.file}, p. ${a.page}`}</a><div className="muted spec-src">&ldquo;{a.quote}&rdquo;</div></td></tr>)}</tbody></table></div>
        {s.review && <p className="muted">{s.review.status === "confirmed" ? "Confirmed" : "Rejected"} by {s.review.by}{s.review.note && `: ${s.review.note}`}</p>}
        {unitRole && <div className="row">
          <button type="button" className="sm" disabled={!!busy} onClick={() => review(s.spec_id, "confirmed")}>Confirm these ratings</button>
          {noteFor !== s.spec_id ? <button type="button" className="secondary sm" disabled={!!busy} onClick={() => setNoteFor(s.spec_id)}>Reject…</button>
            : <form className="inline" action={(f) => review(s.spec_id, "rejected", String(f.get("note") ?? ""))}>
              <label><span className="sr-only">What is wrong</span><input name="note" required placeholder="What is wrong in these ratings" /></label>
              <button className="secondary sm" disabled={!!busy}>Reject</button></form>}
          <span className="muted">Only the family&apos;s own unit can confirm or reject.</span></div>}
      </details>))}
  </section>);
}

export default function ProductDetails({ part }: { part: string }) {
  const { data: d, error, reload } = useApi<ProductDetail>(`/api/catalog/product?part=${encodeURIComponent(part)}`);
  const [broken, setBroken] = useState<Set<string>>(new Set());
  if (error) return <Alert kind="error" title={`Could not load ${part}.`}>{error}</Alert>;
  if (!d) return <Skeleton lines={6} />;
  const web = d.product_type === "web_listing";
  const verified = d.images.filter((i) => i.verified && !broken.has(i.file));
  const pagesFor = (doc: ProductDetail["documents"][number]) => doc.pages[d.family_key ?? ""] ?? doc.pages[d.part_number ?? ""] ?? [];
  return (
    <div className="product-detail">
      <section className="card product-head" data-tour="catalog-detail-head">
        <div className="product-image">{verified.length > 0
          ? <img src={fileUrl(verified[0].file)} alt={`${d.name}: ${verified[0].kind} from ${verified[0].source_file}, page ${verified[0].page}`} onError={() => setBroken(new Set([...broken, verified[0].file]))} />
          : <span className="thumb ph product-ph" role="img" aria-label={d.images.length ? "Image not verified for this product" : "No image in the supplied documents"}>No verified image</span>}</div>
        <div>
          {d.name !== d.part_number && <h2 className="product-name">{d.name}</h2>}
          <p className="row"><StatusBadge status="info" label={TYPE_LABEL[d.product_type ?? "web_listing"]} /> <StatusBadge status={d.status === "Active" || d.status === "Published" ? "pass" : "neutral"} label={d.status ?? "Status unknown"} />
            <StatusBadge status="neutral" label={`Source: ${SOURCE_LABEL[d.source]}`} />{d.in_last_import === false && <StatusBadge status="warn" label="Not in the last spreadsheet" />}</p>
          <p>{d.family ?? "No family"}{d.family_key && !web && <> · series <Link href={link(d.family_key)}>{d.family_key}</Link> on the web catalog</>}
            {d.evaluates && d.evaluates.length > 0 && <> · evaluates {d.evaluates.join(", ")}</>}</p>
          {web && <p>{d.web_text} {d.source_url && <a href={d.source_url} target="_blank" rel="noopener noreferrer">Official page</a>}</p>}
          {!web && d.web && <p className="muted">The web page for the series says: {d.web.specs} (retrieved {d.web.retrieved})</p>}
          {!web && d.verified === false && <p className="muted">Values as exported in the Flex Power Modules spreadsheet, not confirmed by the unit.</p>}
        </div>
      </section>

      {!web && <Specs d={d} />}
      {web ? (d.variants.length > 0 || d.bu === "FPM") && <Related title="Spreadsheet parts of this series" rows={d.variants} empty="The spreadsheet lists no part of this series." />
        : d.product_type === "evaluation_board" ? <Related title="Modules this board evaluates" rows={d.variants} empty="No module of the evaluated series is in the spreadsheet." />
        : <Related title="Evaluation boards for this series" rows={d.variants} empty="No evaluation board for this series in the spreadsheet." />}
      {(d.specs?.length ?? 0) > 0 || web ? <Ratings specs={d.specs ?? []} onDone={reload} /> : null}

      <section className="card" data-tour="catalog-detail-documents"><h2>Documents ({d.documents.length})</h2>
        {d.documents.length === 0 ? <EmptyState title="No supplied document" hint="No supplied datasheet or brochure is tied to this product or its family." /> :
          <ul className="per-req">{d.documents.map((doc) => { const pages = pagesFor(doc);
            return <li key={doc.file}><a href={`${fileUrl(doc.file)}${pages.length ? `#page=${pages[0]}` : ""}`} target="_blank" rel="noopener noreferrer"><strong>{doc.title}</strong></a>
              {" "}<span className="muted">{doc.doc_type.replace("_", "-")} · {doc.publisher} · {doc.applies === "family" ? "about this family" : doc.applies === "part" ? "names this part" : "general"}
                {pages.length > 0 && ` · pages ${pages.join(", ")}`}</span>{doc.note && <div className="muted">{doc.note}</div>}</li>; })}</ul>}
      </section>

      {d.images.length > 0 && <section className="card"><h2>Images ({d.images.length})</h2>
        <div className="product-gallery">{d.images.map((i) => <figure key={i.file}>
          {i.verified && !broken.has(i.file) ? <img src={fileUrl(i.file)} alt={`${i.kind} from ${i.source_file}, page ${i.page}`} loading="lazy" onError={() => setBroken(new Set([...broken, i.file]))} />
            : <span className="thumb ph product-ph" role="img" aria-label="Image not verified">Not verified</span>}
          <figcaption className="muted">{i.kind} · {i.source_file}, p. {i.page}{i.verified ? "" : " · the page does not name this product beside it"}</figcaption></figure>)}</div>
      </section>}
    </div>
  );
}
