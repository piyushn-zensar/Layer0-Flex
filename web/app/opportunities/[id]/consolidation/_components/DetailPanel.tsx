"use client";
// The detail of one matrix row (a requirement and one unit's answer), beside the table.  Owner: Janvia.
// reason, conditions, workaround and next steps are what the unit wrote (A-18); a missing value reads "Not provided".
import Link from "next/link";
import { forwardRef, useState } from "react";
import { StatusBadge } from "@/components/ui";
import ComplianceBadge from "./ComplianceBadge";
import ResponseHistory from "./ResponseHistory";
import SourcePreview from "./SourcePreview";
import { rowKey, type MatrixRow } from "./types";

const NOT_PROVIDED = <span className="muted">Not provided</span>;
// "pending" / "not_assigned" as a label ("Pending", "Not assigned"); the value itself is what the endpoint returned.
const sentence = (value: string) => { const t = value.replace(/_/g, " "); return t.charAt(0).toUpperCase() + t.slice(1); };

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <div className="detail-field"><dt>{label}</dt><dd>{children}</dd></div>;
}

// activityHref: the Activity page filtered to this requirement; historyOpen: the table's "History" link opened this row to show it.
const DetailPanel = forwardRef<HTMLHeadingElement, { row: MatrixRow; docName: string; traceHref: string; activityHref: string; historyOpen: boolean; onClose: () => void }>(
  function DetailPanel({ row, docName, traceHref, activityHref, historyOpen, onClose }, headingRef) {
    const [showSource, setShowSource] = useState(false);
    const text = (v: string | null) => (v && v.trim() ? <span className="detail-text">{v}</span> : NOT_PROVIDED);
    const hasSource = row.spans.some((s) => s.document_id && s.page);
    return (
      <aside className="matrix-detail" aria-label={`Details of ${row.req_id}`} data-tour="matrix-detail">
        <div className="detail-head">
          <div>
            <h3 ref={headingRef} tabIndex={-1}>Requirement <span className="mono">{row.req_id}</span></h3>
            <p className="muted">{row.unit ? `${row.unit} · ${row.unit_name}` : "Not assigned to a unit"}</p>
          </div>
          <button type="button" className="secondary sm" onClick={onClose} aria-label={`Close the details of ${row.req_id}`}>Close</button>
        </div>
        <dl className="detail-list">
          <Field label="Requirement">{text(row.requirement)}</Field>
          <Field label="Quote from the RFP">{row.quote ? <blockquote className="quote">“{row.quote}”</blockquote> : NOT_PROVIDED}</Field>
          <Field label="Category"><span className="tag">{row.category}</span></Field>
          <Field label="Unit">{row.unit ? <>{row.unit} <span className="muted">· {row.unit_name}</span></> : <span className="muted">Not assigned</span>}</Field>
          <Field label="Product">{text(row.product)}</Field>
          <Field label="Requirement state"><StatusBadge status={row.state} label={sentence(row.state)} /></Field>
          <Field label="Assignment state">
            {row.status ? <StatusBadge status={row.status} label={sentence(row.status)} /> : <span className="muted">Not assigned</span>}
            {row.assignments > 1 && <span className="muted"> · held by {row.assignments} units</span>}
          </Field>
          <Field label="Response">{row.response ? <span className="detail-text">{row.response}</span> : <span className="muted">No response yet</span>}</Field>
          <Field label="Compliance">{row.compliance ? <ComplianceBadge row={row} /> : <span className="muted">No compliance yet</span>}</Field>
          <Field label="Reason">{text(row.reason)}</Field>
          <Field label="Conditions">{text(row.conditions)}</Field>
          <Field label="Workaround">{text(row.workaround)}</Field>
          <Field label="Next steps">{text(row.next_steps)}</Field>
          {(row.responded_by || row.validated_by) && (
            <Field label="Answered by">{row.responded_by ?? "—"}{row.validated_by && <span className="muted"> · validated by {row.validated_by}</span>}
              {row.validation_note && <div className="muted">{row.validation_note}</div>}</Field>
          )}
          <Field label="History">
            {row.assignment_id != null
              ? <ResponseHistory assignmentId={row.assignment_id} unit={row.unit} defaultOpen={historyOpen} />
              : <span className="muted">No unit holds this requirement yet, so there is no answer history.</span>}
            <div className="detail-actions"><Link href={activityHref} data-tour="matrix-activity-link">All activity for {row.req_id}</Link></div>
          </Field>
          <Field label="Source">
            {row.source} <span className="muted">· {docName}</span>
            <div className="detail-actions">
              {hasSource
                ? <button type="button" className="secondary sm" aria-expanded={showSource} onClick={() => setShowSource(!showSource)}>{showSource ? "Hide source page" : "Show source page"}</button>
                : null}
              <Link href={traceHref}>Open in Traceability</Link>
            </div>
          </Field>
        </dl>
        {/* keyed by row: the page and its boxes follow the selected row, while "Show source page" stays open */}
        {(showSource || !hasSource) && <SourcePreview key={rowKey(row)} row={row} docName={docName} traceHref={traceHref} />}
      </aside>
    );
  });

export default DetailPanel;
