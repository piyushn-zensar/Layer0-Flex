"""
Module M11 — Provenance & Traceability.

The trust mechanism for Layer 0. An application engineer reviewing a
multi-million-dollar switchgear bid will not accept an asserted value;
they need to see where it came from. This module makes every value the
system emits auditable back to either a location in the customer's
document or the rule that derived it.

THREE PROVENANCE CLASSES
------------------------
EXTRACTED   The value was located verbatim in the source document.
            Carries a full SpanAnchor: doc id, version, page, page-local
            character offsets, the quoted text, and the extractor that
            produced the text.

DERIVED     The value was computed by a rule, not read from the document.
            A tier such as ETO_GUIDED appears nowhere in any RFP — it is
            the output of a rule applied to extracted values. Carries a
            rule id plus the parent anchors it consumed.

UNANCHORED  The value was produced but could NOT be located in the source.
            This happens legitimately when a language model paraphrases
            rather than quoting. The alternative — inventing an offset —
            would be fabricating evidence, so this class exists instead.
            Always carries warning_flag=True and must render as a visible
            warning in the UI, never silently.

OFFSET BASIS
------------
Offsets are PAGE-LOCAL, into the normalised text of that page, produced
by the named `extractor`. Whole-document offsets were rejected because
they shift whenever pagination or extraction changes; page-local offsets
plus a recorded extractor version are reproducible.

PARENT ANCHORS
--------------
Structured objects, never colon-delimited strings. Real procurement
document ids contain colons ("RFP-SYR-2026:REV3"), which would make a
flat string ambiguous to parse. A flat `label` is provided for display
only and must never be parsed.
"""
from dataclasses import dataclass, field, asdict
from typing import Optional
import hashlib
import re


class ProvenanceClass:
    EXTRACTED = "EXTRACTED"
    DERIVED = "DERIVED"
    UNANCHORED = "UNANCHORED"


@dataclass
class DocumentRef:
    """Identifies a specific VERSION of a source document.

    Version binding matters: the Syracuse RFP we test against is Spec
    Rev 3. If extraction ran against Rev 2 and an addendum lands, every
    anchor silently points at stale text unless anchors are bound to a
    version. The content hash gives tamper-evidence at the document
    level (which is what a hash is actually good for — it cannot drive
    a visual highlight, which is why anchors are spans, not hashes).
    """
    doc_id: str
    version: str = "unversioned"
    filename: Optional[str] = None
    content_sha256: Optional[str] = None
    extractor: str = "inline-text"

    @staticmethod
    def hash_content(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def to_dict(self):
        return asdict(self)


@dataclass
class SpanAnchor:
    """A locatable position in a source document.

    `span` is [start, end) into the normalised text of `page`, as
    produced by DocumentRef.extractor.
    """
    doc_id: str
    version: str
    page: int
    span: tuple
    quote: str
    extractor: str = "inline-text"

    def to_dict(self):
        return {
            "doc_id": self.doc_id,
            "version": self.version,
            "page": self.page,
            "span": [self.span[0], self.span[1]],
            "quote": self.quote,
            "extractor": self.extractor,
        }

    @property
    def label(self) -> str:
        """Display-only. MUST NOT be parsed — doc ids may contain colons."""
        return f"{self.doc_id} {self.version} p{self.page} [{self.span[0]}:{self.span[1]}]"


@dataclass
class Provenance:
    """Attached to every parameter the system emits."""
    provenance_class: str
    anchor: Optional[SpanAnchor] = None
    rule_id: Optional[str] = None
    parent_anchors: list = field(default_factory=list)
    reason: Optional[str] = None
    warning_flag: bool = False

    def to_dict(self):
        out = {"class": self.provenance_class}
        if self.provenance_class == ProvenanceClass.EXTRACTED and self.anchor:
            out["anchor"] = self.anchor.to_dict()
        elif self.provenance_class == ProvenanceClass.DERIVED:
            out["rule_id"] = self.rule_id
            out["parent_anchors"] = [a.to_dict() for a in self.parent_anchors]
        if self.reason:
            out["reason"] = self.reason
        if self.warning_flag:
            out["warning_flag"] = True
        return out


def extracted(anchor: SpanAnchor) -> Provenance:
    return Provenance(ProvenanceClass.EXTRACTED, anchor=anchor)


def derived(rule_id: str, parent_anchors: list = None, reason: str = None) -> Provenance:
    return Provenance(
        ProvenanceClass.DERIVED,
        rule_id=rule_id,
        parent_anchors=parent_anchors or [],
        reason=reason,
    )


def unanchored(reason: str) -> Provenance:
    return Provenance(
        ProvenanceClass.UNANCHORED,
        reason=reason,
        warning_flag=True,
    )


def parameter(name: str, value, prov: Provenance) -> dict:
    """The universal shape for any provenanced value in a payload."""
    return {"parameter": name, "value": value, "provenance": prov.to_dict()}


# ---------------------------------------------------------------------
# Anchoring helpers
# ---------------------------------------------------------------------

def _normalise(text: str) -> str:
    """Whitespace normalisation applied before offset calculation. Offsets
    are into THIS representation, which is why the extractor is recorded."""
    return re.sub(r"[ \t]+", " ", text)


def paginate(text: str, page_size_chars: int = 3000) -> list:
    """Splits inline text into pseudo-pages so page-local offsets exist
    even when the input is pasted text rather than a real PDF. A real
    PDF ingestion (M1) supplies genuine page boundaries and replaces
    this. Splitting only on line boundaries keeps quotes intact."""
    pages, current, count = [], [], 0
    for line in _normalise(text).split("\n"):
        if count + len(line) + 1 > page_size_chars and current:
            pages.append("\n".join(current))
            current, count = [], 0
        current.append(line)
        count += len(line) + 1
    if current:
        pages.append("\n".join(current))
    return pages or [""]


def anchor_quote(quote: str, pages: list, doc: DocumentRef) -> Optional[SpanAnchor]:
    """Locates `quote` in the paginated source and returns a SpanAnchor,
    or None if it cannot be found verbatim.

    Returning None rather than a best guess is deliberate: a wrong anchor
    is worse than an absent one, because it looks authoritative. Callers
    convert None into an UNANCHORED provenance.
    """
    if not quote:
        return None
    needle = _normalise(quote).strip()
    if not needle:
        return None

    for page_no, page_text in enumerate(pages, start=1):
        idx = page_text.find(needle)
        if idx == -1:
            # try case-insensitive as a second pass
            lowered = page_text.lower().find(needle.lower())
            if lowered == -1:
                continue
            idx = lowered
        return SpanAnchor(
            doc_id=doc.doc_id,
            version=doc.version,
            page=page_no,
            span=(idx, idx + len(needle)),
            quote=page_text[idx:idx + len(needle)],
            extractor=doc.extractor,
        )
    return None


def provenance_for_quote(quote: Optional[str], pages: list, doc: DocumentRef,
                         param_name: str) -> Provenance:
    """Convenience: anchor a quote, degrading to UNANCHORED when the
    verbatim string cannot be located."""
    if not quote:
        return unanchored(
            f"No source quote was captured for '{param_name}'; value could not be located in the document."
        )
    a = anchor_quote(quote, pages, doc)
    if a is None:
        return unanchored(
            f"Value for '{param_name}' was produced from a paraphrase; exact string match against the source failed."
        )
    return extracted(a)


# ---------------------------------------------------------------------
# Bi-directional index
# ---------------------------------------------------------------------

def build_index(parameters: list) -> dict:
    """Bi-directional lookup supporting the dual-view workspace.

    forward  : page number -> parameters sourced from that page
               (engineer reading the original doc sees what was parsed)
    backward : parameter name -> its anchor
               (engineer clicking a value jumps to the source text)
    unanchored: parameters with no source location, surfaced explicitly
    """
    forward, backward, unanchored_list = {}, {}, []
    for p in parameters:
        prov = p.get("provenance", {})
        cls = prov.get("class")
        name = p.get("parameter")
        if cls == ProvenanceClass.EXTRACTED and prov.get("anchor"):
            page = prov["anchor"]["page"]
            forward.setdefault(page, []).append(name)
            backward[name] = prov["anchor"]
        elif cls == ProvenanceClass.UNANCHORED:
            unanchored_list.append({"parameter": name, "reason": prov.get("reason")})
    return {
        "forward_by_page": forward,
        "backward_by_parameter": backward,
        "unanchored": unanchored_list,
        "coverage": {
            "total": len(parameters),
            "anchored": len(backward),
            "unanchored": len(unanchored_list),
        },
    }
