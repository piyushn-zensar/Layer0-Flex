"""Document ID and Document Instance ID of a file (C-27, decided 15 Oct 2026). Shared by bids (opportunities) and the
knowledge sources: the identifiers the authoring tool embedded in the file, else its SHA-256 fingerprint for both.

    identity(data, suffix) -> (document_id, instance_id, id_source)   id_source: "embedded" | "fingerprint"

PDF: the two entries of the trailer /ID (the first stays for the document's life, the second changes with each save),
else xmpMM:DocumentID / xmpMM:InstanceID from the XMP metadata. Word: the document ID in word/settings.xml (Word keeps
no instance ID, so the exact file is the instance). Anything else (spreadsheets, web pages, text): the fingerprint.
Embedded IDs are written by the authoring tool: some tools omit or reuse them, hence the fallback.
"""
import hashlib
import io
import re
import zipfile

import pymupdf


def identity(data: bytes, suffix: str) -> tuple[str, str, str]:
    sha = hashlib.sha256(data).hexdigest()
    suffix = suffix.lower()
    if suffix == ".pdf":
        try:
            with pymupdf.open(stream=data, filetype="pdf") as pdf:
                kind, value = pdf.xref_get_key(-1, "ID")
                ids = re.findall(r"<([0-9A-Fa-f]+)>", value) if kind == "array" else []
                if len(ids) == 2:
                    return ids[0].upper(), ids[1].upper(), "embedded"
                xmp = pdf.get_xml_metadata() or ""
        except RuntimeError:  # damaged PDF: the reader reports it later; identify it by its bytes
            xmp = ""
        doc, inst = (re.search(rf"xmpMM:{t}(?:>|=\")([^<\"]+)", xmp) for t in ("DocumentID", "InstanceID"))
        if doc and inst:
            return doc.group(1), inst.group(1), "embedded"
    if suffix == ".docx":
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                settings = z.read("word/settings.xml").decode("utf-8", "replace") if "word/settings.xml" in z.namelist() else ""
        except zipfile.BadZipFile:
            settings = ""
        found = re.search(r"w15:docId w15:val=\"([^\"]+)\"", settings) or re.search(r"w14:docId w14:val=\"([^\"]+)\"", settings)
        if found:
            return found.group(1), sha, "embedded"
    return sha, sha, "fingerprint"
