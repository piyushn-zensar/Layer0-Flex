"""P-28 spike (C-18): Word and Excel documents are read through a rendered PDF, so pages, lines, anchoring and page
images work as for a PDF; other types are still recorded but not read.

Run:  .venv\\Scripts\\python -m pytest -q tests/test_p28_office.py
"""
import io
import os
import tempfile
import zipfile

os.environ["STORE_DIR"] = tempfile.mkdtemp()
os.environ["LLM_PROVIDER"] = "mock"

from conftest import signed_in  # noqa: E402
from openpyxl import Workbook  # noqa: E402

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def xlsx() -> bytes:
    book = Workbook()
    book.active.title = "Data sheet"
    for row in (["Description", "Requirement", "Units"], ["Rated maximum voltage", 15, "kV rms"],
                ["Basic impulse level", 95, "kV peak"]):
        book.active.append(row)
    out = io.BytesIO()
    book.save(out)
    return out.getvalue()


def docx() -> bytes:
    xml = (f'<w:document xmlns:w="{W}"><w:body>'
           '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>2.1 Switchgear</w:t></w:r></w:p>'
           '<w:p><w:r><w:t>The switchgear shall be arc-resistant Type 2B to IEEE C37.20.7.</w:t></w:r></w:p>'
           '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>2.2 Relays</w:t></w:r></w:p>'
           '<w:p><w:r><w:t>Protective relays shall be microprocessor based.</w:t></w:r></w:p>'
           '<w:sectPr/></w:body></w:document>')
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr("word/document.xml", xml)
    return out.getvalue()


def test_word_and_excel_are_read_like_a_pdf():
    client = signed_in()
    opp = client.post("/api/opportunities", json={"title": "office"}).json()["id"]
    url = f"/api/opportunities/{opp}"
    sheet = client.post(f"{url}/documents", files={"file": ("datasheet.xlsx", xlsx())}).json()
    word = client.post(f"{url}/documents", files={"file": ("spec.docx", docx())}, data={"role": "other"}).json()
    cad = client.post(f"{url}/documents", files={"file": ("plan.dwg", b"AC1027")}, data={"role": "other"}).json()
    docs = {d["filename"]: d for d in client.get(url).json()["documents"]}
    assert docs["datasheet.xlsx"]["status"] == "ingested" and docs["datasheet.xlsx"]["page_count"] == 1
    assert docs["spec.docx"]["status"] == "ingested" and docs["spec.docx"]["page_count"] == 2  # a page per heading 1
    assert docs["plan.dwg"]["status"] == "unsupported" and cad["filename"] == "plan.dwg"  # recorded, not read

    page = client.get(f"/api/documents/{sheet['id']}/pages/1").json()
    assert [l["text"] for l in page["lines"]][:3] == ["Sheet: Data sheet", "Description | Requirement | Units",
                                                      "Rated maximum voltage | 15 | kV rms"]
    assert client.get(f"/api/documents/{sheet['id']}/pages/1.png").content[:4] == b"\x89PNG"
    second = client.get(f"/api/documents/{word['id']}/pages/2").json()
    assert [l["text"] for l in second["lines"]] == ["2.2 Relays", "Protective relays shall be microprocessor based."]

    # anchoring works unchanged: a quote from the data sheet enters the register with its page and line
    req = client.post(f"{url}/requirements", json={"quote": "Rated maximum voltage: 15 kV rms", "page": 1}).json()
    assert (req["status"], req["source"]) == ("approved", "p. 1, line 3"), req
