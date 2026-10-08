"""Find a quote on a page and return its line range and highlight boxes. Never invents a location (rule R1)."""
import re
import unicodedata

_PUNCT = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"',
                        "‐": "-", "‑": "-", "–": "-", "—": "-", " ": " "})


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text).translate(_PUNCT)).strip().lower()


def find(quote: str, pages: list[dict], hint_page: int | None = None) -> dict | None:
    """pages: layout-model pages. Returns {"page", "line_start", "line_end", "bboxes"} or None.
    ponytail: a quote must sit on one page; split cross-page quotes into two requirements."""
    needle = normalise(quote)
    if not needle:
        return None
    ordered = sorted(pages, key=lambda p: p["page"] != hint_page)  # hinted page first
    for page in ordered:
        starts, text = [], ""
        for line in page["lines"]:
            starts.append(len(text))
            text += normalise(line["text"]) + " "
        at = text.find(needle)
        if at < 0:
            continue
        end = at + len(needle)
        hit = [l for l, s in zip(page["lines"], starts) if s < end and s + len(normalise(l["text"])) > at]
        return {"page": page["page"], "line_start": hit[0]["n"], "line_end": hit[-1]["n"],
                "bboxes": [l["bbox"] for l in hit]}
    return None


if __name__ == "__main__":  # self-check: python -m app.modules.requirements.anchoring
    pages = [{"page": 5, "lines": [{"n": 1, "text": "Switchgear shall be Arc‐resistant", "bbox": [0, 0, 1, 1]},
                                   {"n": 2, "text": "Type  2B.", "bbox": [0, 2, 1, 3]}]}]
    assert find("switchgear shall be arc-resistant type 2B.", pages) == {
        "page": 5, "line_start": 1, "line_end": 2, "bboxes": [[0, 0, 1, 1], [0, 2, 1, 3]]}
    assert find("not on the page", pages) is None
    print("anchoring ok")
