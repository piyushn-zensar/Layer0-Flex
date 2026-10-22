"""P-45 (C-43): the Compliant with changes outcome (stored "deviation"). It needs a reason and the proposed change
(the workaround field); it is labelled in the matrix, the exports and the hand-off, and the Bid decision counts the
four reviewed outcomes separately."""
import csv
import io
import os
import tempfile

os.environ["STORE_DIR"] = tempfile.mkdtemp()

import pytest  # noqa: E402

from conftest import auth, signed_in  # noqa: E402

CHANGES = "Say what changes from the requested specification"


def test_deviation_answer_validation_exports_and_bid_decision():
    from app.core.db import SessionLocal
    from app.modules.workpackages import service as workpackages
    from scripts import seed_demo

    seed_demo.main()
    client, crown = signed_in(), auth("crown.de")
    opp = client.get("/api/portfolio").json()[0]["opp"]["id"]
    base = f"/api/bids/{opp}"
    held = {}
    for r in client.get(f"{base}/compliance-matrix").json()["rows"]:
        held.setdefault(r["req_id"], []).append(r["unit"])
    item = next(i for i in client.get("/api/inbox/CROWN", headers=crown).json()["items"]
                if i["opportunity_id"] == opp and i["may"]["answer"] and held[i["req_id"]] == ["CROWN"])
    url = f"/api/assignments/{item['id']}/respond"

    # 1. answering: a reason and the proposed change are both required
    answer = {"compliance": "deviation", "response": "Offered at 480 V", "reason": "The RFP asks 415 V"}
    assert client.post(url, json={**answer, "reason": ""}, headers=crown).status_code == 422
    r = client.post(url, json={**answer, "workaround": "  "}, headers=crown)
    assert r.status_code == 422 and CHANGES in r.text
    with SessionLocal() as db, pytest.raises(ValueError, match=CHANGES):
        workpackages.respond(db, item["id"], "deviation", None, "", {"name": "Crown Design Engineer", "role": "design_engineer",
                                                                     "bu": "CROWN"}, reason="x")
    answer["workaround"] = "480 V lineup with a step-down transformer"
    assert client.post(url, json=answer, headers=crown).status_code == 200
    inbox = client.get("/api/inbox/CROWN").json()
    assert "deviation" in inbox["compliance"]
    row = next(i for i in inbox["items"] if i["id"] == item["id"])
    assert row["compliance"] == "deviation" and row["workaround"] == answer["workaround"]

    # 2. validated: the matrix, the CSV and the hand-off name the outcome
    assert client.post(f"/api/assignments/{item['id']}/validate", json={"ok": True}, headers=auth("crown.pm")).status_code == 200
    m = next(r for r in client.get(f"{base}/compliance-matrix").json()["rows"] if r["assignment_id"] == item["id"])
    assert m["compliance_label"] == "Compliant with changes" and m["workaround"] == answer["workaround"]
    rows = list(csv.reader(io.StringIO(client.get(f"{base}/compliance-matrix.csv").text.lstrip("﻿"))))
    head, mine = rows[0], next(r for r in rows[1:] if r[0] == item["req_id"] and r[5] == "CROWN")
    assert mine[head.index("Compliance")] == "Compliant with changes" and mine[head.index("Proposed change")] == answer["workaround"]
    handoff = client.get(f"{base}/handoff/CROWN").json()
    ua = [i["unit_answer"] for r in handoff["routes"].values() for i in r["items"] if i["req_id"] == item["req_id"]]
    assert ua and ua[0]["compliance_label"] == "Compliant with changes"

    # 3. the Bid decision counts each outcome; the compliance position counts it per unit
    s = client.get(f"{base}/decisions").json()["summary"]
    assert set(s["compliance"]) == {"met", "partial", "deviation", "not_met"} and item["req_id"] in s["compliance"]["deviation"]
    crit = next(c for c in s["criteria"] if c["id"] == "compliance")
    assert "compliant with changes" in crit["detail"], crit
    assert all("changes" in levels for levels in s["by_category"].values())
    assert client.get(f"{base}/schedule").json()["compliance"]["CROWN"]["deviation"] == 1


def test_customer_word_ranks_deviation_between_partial_and_compliant():
    from types import SimpleNamespace as NS

    from app.modules.consolidation import excel

    def word(*values):
        return excel.customer_compliance([NS(status="validated", compliance=v) for v in values])
    assert word("partial", "deviation") == "Partially compliant" and word("deviation", "met") == "Compliant with changes"
