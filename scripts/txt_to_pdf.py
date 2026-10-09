"""Turn a plain-text sample RFP into a PDF with a real text layer, so it runs through the normal reader flow (task A-08).

    .venv\\Scripts\\python -m scripts.txt_to_pdf data/RFP/samples/rfp_hyperscale_campus.txt

Writes the PDF next to the text file. Deterministic: the same text gives the same bytes (no dates, fixed file ID),
so the document hash, line numbers and highlights stay the same on every machine.
"""
import sys
from pathlib import Path

import pymupdf

PAGE = pymupdf.paper_rect("letter")
MARGIN, FONT_SIZE, LEADING = 72, 10.5, 15  # points; one text line per RFP line keeps line numbers meaningful


def convert(txt: Path) -> Path:
    lines = txt.read_text("utf-8").splitlines()
    pdf = pymupdf.open()
    page, y = None, 0.0
    width = PAGE.width - 2 * MARGIN
    for raw in lines:
        # wrap long lines by width so nothing runs off the page; each wrapped piece is its own PDF line
        words, pieces, cur = raw.split(" "), [], ""
        for w in words:
            test = f"{cur} {w}".strip()
            if pymupdf.get_text_length(test, fontname="helv", fontsize=FONT_SIZE) > width and cur:
                pieces.append(cur)
                cur = w
            else:
                cur = test
        pieces.append(cur)
        for piece in pieces:
            if page is None or y > PAGE.height - MARGIN:
                page, y = pdf.new_page(width=PAGE.width, height=PAGE.height), MARGIN
            if piece:
                page.insert_text((MARGIN, y), piece, fontname="helv", fontsize=FONT_SIZE)
            y += LEADING
    pdf.set_metadata({"title": txt.stem, "producer": "scripts/txt_to_pdf.py", "creator": "Layer 0",
                      "creationDate": "", "modDate": ""})
    out = txt.with_suffix(".pdf")
    pdf.save(out, garbage=4, deflate=True, no_new_id=True)
    return out


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        print("wrote", convert(Path(arg)))
