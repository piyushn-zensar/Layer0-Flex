"""Find a quote in the layout pages and return where it is. Never invents a location (rule R1).

The document is one stream of words from its body lines (page furniture left out, as the reader never sees it), so a
quote may continue across a line or a page break: each page it touches is one span. Words must be exact and in order;
case, typographic quotes and dashes, whitespace and punctuation between words are ignored (a table row read as
"System nominal voltage: 13.2 kV" is still verbatim), and so are hyphens inside a word, so a word hyphenated at a line
break ("resis-" / "tant") matches "resistant". When the wording occurs more than once, the occurrence nearest to the
reader's line references wins (else the hinted page, else the first).

With line references, a quote the reader stitched from its cited lines (a list's lead-in and one item, without the
"1." between) is verified as up to MAX_FRAGMENTS in-order pieces of those lines, each a span.
C-03, technical-architecture section 16.4.
"""
import bisect
import re
import unicodedata

_PUNCT = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"',
                        "‐": "-", "‑": "-", "–": "-", "—": "-", " ": " "})
_IN_WORD_HYPHEN = re.compile(r"(?<=\w)- ?(?=\w)")  # "arc-resistant", and "resis- tant" in a quote copied over a break
MAX_FRAGMENTS = 4      # pieces of the cited lines one quote may be stitched from
MIN_FRAGMENT_WORDS = 2  # a piece shorter than this proves nothing
MARGIN = 1              # cited line numbers may be one off


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text).translate(_PUNCT)).strip().lower()


def _words(text: str) -> list[str]:
    return re.findall(r"\w+", _IN_WORD_HYPHEN.sub("", normalise(text)))


_last: list = []  # [(pages, index)]: the last document indexed; extraction anchors hundreds of quotes in one document


def _index(pages: list[dict]):
    """(words, [(first line, last line) of each word], [(page, line)], " "-joined words, start offset of each word)."""
    words, owners, lines = [], [], []
    if _last and _last[0][0] is pages:
        return _last[0][1]
    for page in sorted(pages, key=lambda p: p["page"]):
        for line in page["lines"]:
            text = "" if line.get("furniture") else normalise(line["text"])
            if not text:
                continue
            n = len(lines)
            lines.append((page, line))  # a line of punctuation only ("•") has no words but stays inside a span
            found = _words(text)
            if not found:
                continue
            if words and words[-1].endswith("-"):  # hyphenated at the end of the previous line: one word
                words[-1] = words[-1][:-1] + found.pop(0)
                owners[-1] = (owners[-1][0], n)
            words += found
            owners += [(n, n)] * len(found)
            if re.search(r"\w-$", text):
                words[-1] += "-"
    words = [w.rstrip("-") if i == len(words) - 1 else w for i, w in enumerate(words)]
    starts, at = [], 0
    for w in words:
        starts.append(at)
        at += len(w) + 1
    bare = set(range(len(lines))) - {i for pair in owners for i in pair}  # lines of punctuation only
    built = (words, owners, lines, " ".join(words), starts, bare)
    _last[:] = [(pages, built)]
    return built


def find(quote: str, pages: list[dict], hint_page: int | None = None, lines: list[dict] | None = None) -> dict | None:
    """pages: layout-model pages; lines: the reader's line references [{"page", "first", "last"}].
    Returns {"page", "line_start", "line_end", "bboxes", "spans"} or None. "spans" holds one
    {"page", "line_start", "line_end", "bboxes"} per page (or stitched piece) of the quote; the other keys repeat the
    first span."""
    words, owners, index, text, starts, bare = _index(pages)
    needle = _words(quote)
    if not needle:
        return None
    hits = _occurrences(needle, text, starts)
    if hits:
        first, last = min(hits, key=lambda h: _distance(index[owners[h[0]][0]], hint_page, lines))
        lo, hi = _with_punctuation(normalise(quote), owners[first][0], owners[last][1], index, bare)
        return _spans([list(range(lo, hi + 1))], index)
    pieces = _stitched(needle, words, owners, index, lines) if lines else None
    return _spans(pieces, index) if pieces else None


def _with_punctuation(quote: str, lo: int, hi: int, index: list, bare: set) -> tuple[int, int]:
    """Widens a hit over the punctuation-only lines ("." or "•") next to it that the quote itself starts or ends
    with, beyond the punctuation of its own first and last lines (whitespace ignored)."""
    squeeze = lambda t: re.sub(r"\s", "", t)
    text_of = lambda i: normalise(index[i][1]["text"])
    lead, own = squeeze(re.match(r"\W*", quote).group()), squeeze(re.match(r"\W*", text_of(lo)).group())
    lead = lead[:len(lead) - len(own)] if lead.endswith(own) else lead
    while lead and lo - 1 in bare and index[lo - 1][0] is index[lo][0] and lead.endswith(t := squeeze(text_of(lo - 1))):
        lo, lead = lo - 1, lead[:-len(t)]
    tail, own = squeeze(re.search(r"\W*$", quote).group()), squeeze(re.search(r"\W*$", text_of(hi)).group())
    tail = tail[len(own):] if tail.startswith(own) else tail
    while tail and hi + 1 in bare and index[hi + 1][0] is index[hi][0] and tail.startswith(t := squeeze(text_of(hi + 1))):
        hi, tail = hi + 1, tail[len(t):]
    return lo, hi


HINT_MIN_SHARE = 0.8  # share of the quote's words that must be on the claimed page for a location hint


def hint(quote: str, pages: list[dict], hint_page: int | None = None, lines: list[dict] | None = None) -> dict | None:
    """For a quote that find() could not verify: where the reader says it is, when the page backs that up.
    Returns {"page", "line_start", "line_end", "share"} (lines None without line references) or None when fewer than
    HINT_MIN_SHARE of the quote's words are on that page. A hint is never a source: it only says where to look."""
    page_no = lines[0]["page"] if lines else hint_page
    page = next((p for p in pages if p["page"] == page_no), None)
    needle = _words(quote)
    if page is None or not needle:
        return None
    on_page = {w for line in page["lines"] if not line.get("furniture") for w in _words(line["text"])}
    share = sum(w in on_page for w in needle) / len(needle)
    if share < HINT_MIN_SHARE:
        return None
    numbers = [l["n"] for l in page["lines"]]
    cited = [r for r in lines or [] if r["page"] == page_no]
    first, last = (max(min(numbers), cited[0]["first"]), min(max(numbers), cited[-1]["last"])) if cited else (None, None)
    return {"page": page_no, "line_start": first, "line_end": last, "share": round(share, 2)}


def _occurrences(needle: list[str], text: str, starts: list[int]) -> list[tuple[int, int]]:
    """(first, last) word of every whole-word occurrence."""
    probe, hits = " ".join(needle), []
    at = text.find(probe)
    while at >= 0:
        end = at + len(probe)
        if (at == 0 or text[at - 1] == " ") and (end == len(text) or text[end] == " "):
            first = bisect.bisect_right(starts, at) - 1
            hits.append((first, first + len(needle) - 1))
        at = text.find(probe, at + 1)
    return hits


def _distance(first: tuple[dict, dict], hint_page: int | None, lines: list[dict] | None) -> tuple[int, int]:
    page, line = first[0]["page"], first[1]["n"]
    if lines:
        return abs(page - lines[0]["page"]), abs(line - lines[0]["first"])
    return (abs(page - hint_page), 0) if hint_page is not None else (0, 0)  # min() keeps the first of equals


def _stitched(needle: list[str], words: list[str], owners: list, index: list, lines: list[dict]) -> list[list[int]] | None:
    """The quote as in-order pieces of the cited lines (greedy, longest piece first), or None. Only whole lines may be
    left out between pieces (and a list marker such as "1." or "a." starting the next line), never words inside a
    sentence: dropping "not" from "shall not" must not verify."""
    cited = {i for i, (page, line) in enumerate(index)
             if any(r["page"] == page["page"] and r["first"] - MARGIN <= line["n"] <= r["last"] + MARGIN for r in lines)}
    window = [w for w, (a, _) in enumerate(owners) if a in cited]
    line_end = lambda w: w + 1 == len(words) or owners[w + 1][0] != owners[w][1]
    line_start = lambda w: w == 0 or owners[w - 1][1] != owners[w][0]
    marker = lambda w: line_start(w - 1) and len(words[w - 1]) <= 3 and owners[w - 1][1] == owners[w][0]
    pieces, at, pos = [], 0, 0  # at: next needle word; pos: next window position
    while at < len(needle):
        best = None
        for start in range(pos, len(window)):
            if pieces and not (line_start(window[start]) or marker(window[start])):
                continue
            k = 0
            while (at + k < len(needle) and start + k < len(window) and window[start + k] == window[start] + k
                   and words[window[start + k]] == needle[at + k]):
                k += 1
            while k and at + k < len(needle) and not line_end(window[start + k - 1]):
                k -= 1  # a piece that leaves words after it must end with its line
            if k >= MIN_FRAGMENT_WORDS and (best is None or k > best[1]):
                best = (start, k)
        if best is None or len(pieces) == MAX_FRAGMENTS:
            return None
        start, k = best
        first, last = window[start], window[start + k - 1]
        pieces.append(list(range(owners[first][0], owners[last][1] + 1)))
        at, pos = at + k, start + k
    return pieces


def _spans(pieces: list[list[int]], index: list) -> dict:
    """One span per page of each piece; touching pieces on the same page become one span."""
    spans = []
    for piece in pieces:
        for i in piece:
            page, line = index[i]
            last = spans[-1] if spans else None
            if last and last["page"] == page["page"] and (last["_i"] == i or (last["_i"] == i - 1)):
                if last["_i"] != i:
                    last["line_end"], last["_i"] = line["n"], i
                    last["bboxes"].append(line["bbox"])
                continue
            spans.append({"page": page["page"], "line_start": line["n"], "line_end": line["n"],
                          "bboxes": [line["bbox"]], "_i": i})
    for s in spans:
        del s["_i"]
    return spans[0] | {"spans": spans}


if __name__ == "__main__":  # self-check: python -m app.modules.requirements.anchoring
    box = lambda n: [0, n, 1, n + 1]
    page = lambda no, *texts, furniture=(): {"page": no, "lines": [
        {"n": n, "text": t, "bbox": box(n), "furniture": n in furniture} for n, t in enumerate(texts, 1)]}
    pages = [page(5, "Switchgear shall be Arc‐resistant", "Type  2B.")]
    assert find("switchgear shall be arc-resistant type 2B.", pages) == {
        "page": 5, "line_start": 1, "line_end": 2, "bboxes": [box(1), box(2)],
        "spans": [{"page": 5, "line_start": 1, "line_end": 2, "bboxes": [box(1), box(2)]}]}
    assert find("not on the page", pages) is None
    assert find("Switchgear shall be Arc-resistant.", pages)["line_end"] == 1  # added full stop tolerated
    assert find("Switchgear shall be Arc-proof.", pages) is None                # changed words are not
    assert find("Switchgear shall", pages) and find("gear shall", pages) is None  # whole words only
    # a word hyphenated at a line break, quoted joined; and an in-word hyphen broken at the line end
    hyph = [page(7, "The enclosure shall be weather-resis-", "tant and arc-", "resistant to IEEE C37.20.7.")]
    assert find("shall be weather-resistant and arc-resistant", hyph)["line_end"] == 3
    assert find("weather-resis- tant and arcresistant to ieee", hyph)["spans"][0]["line_start"] == 1
    # a table read as "label: value" (the colon is not in the RFP)
    table = [page(74, "Ratings", "System nominal voltage", "13.2", "kV", "Rated Maximum Voltage")]
    assert find("System nominal voltage: 13.2 kV", table)["spans"] == [
        {"page": 74, "line_start": 2, "line_end": 4, "bboxes": [box(2), box(3), box(4)]}]
    # across a page break, without the footer and header in between: two spans
    cross = [page(8, "Body.", "The vendor shall deliver all", "Page 8 of 9", furniture={3}),
             page(9, "RFP 2023-20", "drawings within 30 days.", furniture={1})]
    hit = find("The vendor shall deliver all drawings within 30 days.", cross)
    assert [(s["page"], s["line_start"], s["line_end"]) for s in hit["spans"]] == [(8, 2, 2), (9, 2, 2)], hit
    assert (hit["page"], hit["bboxes"]) == (8, [box(2)])
    # the same wording twice: the occurrence nearest to the reader's lines, else the hinted page, else the first
    twice = [page(3, "Tube of contact lubricant"), page(6, "x", "y", "Tube of contact lubricant", "z",
                                                         "Tube of contact lubricant")]
    assert find("tube of contact lubricant", twice)["page"] == 3
    assert find("tube of contact lubricant", twice, hint_page=6)["line_start"] == 3
    assert find("tube of contact lubricant", twice, 6, [{"page": 6, "first": 5, "last": 5}])["line_start"] == 5
    # a lead-in and one list item, stitched by the reader: verified only within the cited lines, two spans
    items = [page(55, "B.", "Work in this Specification includes, the following items:", "1.",
                  "One (1) 15kV two (2) section Metal Clad Switchgear lineup.", "2.", "Protective Relays and Controls.")]
    quote = "Work in this Specification includes, the following items: Protective Relays and Controls."
    assert find(quote, items) is None                                            # not one passage
    hit = find(quote, items, 55, [{"page": 55, "first": 2, "last": 6}])
    assert [(s["line_start"], s["line_end"]) for s in hit["spans"]] == [(2, 2), (6, 6)], hit
    assert find(quote, items, 55, [{"page": 55, "first": 6, "last": 6}]) is None  # the lead-in is not cited
    assert find("Work in this Protective Relays", items, 55, [{"page": 55, "first": 1, "last": 6}]) is None  # mid-line
    # a list item after its marker ("a."), and a word dropped inside a sentence, which must not verify
    eeo = [page(20, "4. The Contractor’s EEO policy statement shall include the following language:",
                "a. The Contractor will not discriminate against any employee.")]
    cite = [{"page": 20, "first": 1, "last": 2}]
    assert find("The Contractor's EEO policy statement shall include the following language: The Contractor will not "
                "discriminate against any employee.", eeo, 20, cite)["spans"][0]["line_end"] == 2
    assert find("The Contractor will discriminate against any employee.", eeo, 20, cite) is None
    # a location hint for what find() cannot verify, only where the page backs up the reader's claim
    assert hint("The Contractor will discriminate against any employee.", eeo, 20, cite) == {
        "page": 20, "line_start": 1, "line_end": 2, "share": 1.0}
    assert hint("The Contractor will discriminate against any employee.", eeo, 20) == {
        "page": 20, "line_start": None, "line_end": None, "share": 1.0}
    assert hint("The vendor shall paint the switchgear purple.", eeo, 20) is None  # not this page's words
    assert hint("Anything", eeo, 99) is None and hint("Anything", eeo) is None
    print("anchoring ok")
