"""The demo workflow on RC-1 (P-49, C-45): drives the REAL API in-process (FastAPI TestClient on app.main.app), signed
in as the demo accounts of data/accounts.json with DEMO_PASSWORD (.env), against the database the seed uses.

    $env:LLM_PROVIDER="mock"; .venv\\Scripts\\python -m scripts.seed_demo --reset   # seeds, then runs this (A + B)
    $env:LLM_PROVIDER="mock"; .venv\\Scripts\\python -m scripts.run_demo_workflow   # the same, right after a fresh seed
    ... -m scripts.run_demo_workflow --dump <file.json>                            # only writes the dispatched work

Run it on a fresh seed (scripts.seed_demo --reset): RC-1 is OPP-0003 there, matched right after its automatic freeze.
Every step is a person's action through the API, by the role the API allows; each one first re-checks the live
register (the quote it expects) and stops on a surprise, so a changed reading or matcher answer cannot slip through.

Part A (P-49 first half):
  1. the bid manager corrects the reading, with reasons (CORRECTIONS): a missed sentence, five requirements cut at
     page breaks (L3.11, CT-02, L2.09, L4.11, IF-09: each completed, a tail read as its own item excluded),
     categories (evaluation rules, legal and Owner statements tagged compliance; warranty and liability tagged
     technical; technical items tagged submission or staffing; BQ-09 answered once by the bid desk). Each correction
     is a new frozen version; new and
     changed items are matched again (in mock mode the new prompts have no frozen answer: retrieval only)
  2. the units' designers / engineers confirm the matches that are right and correct the others (SOLUTIONS), each
     correction with its reason as a comment on the requirement (P-44: only they accept or change a technical match)
  3. the bid manager reviews the Assessment Summary, enters the RFP due date (DUE_DATE), records participation,
     routes the items without a unit to the teams (the receiving unit's engineer then sets the solution) or records a
     capability gap (customer-facing "Not offered in this tender: ..." with the internal rationale as a comment), and
     sends for assessment (dispatch); nothing may be left needing an owner
  1b. (P-59, C-62) the bid manager applies the synthetic Addendum No. 1 (rc1_addendum_1: L4.13 to L4.15, the compute
     trays' 54 VDC to 12 VDC board converters), confirmed as read; its new items are matched like any change
  4. (P-58, P-59) the unit managers publish their supplied product documents as product evidence, and the bid manager
     runs the product configurator (Technical Requirement Matching: components, part-level and published-ratings
     searches, explanations)
  New steps have no frozen answers until run once with --live-new-steps (Azure): only the addendum, the matching of its
  items and the configurator then call the model; every other step stays in mock mode, so the recorded state holds.
Part B (P-49 second half, part_b()): the units' and the bid desk's placeholder answers (data/seed/rc1_answers),
the delivery estimates and factors, validation (one answer returned with a question and answered again), the bid
manager's approvals, a knowledge-base assessment run (retrieval only) and the go/no-go, which moves the bid to
consolidating. end_state() reads the figures the demo shows. The response outline replays
its frozen drafts (generated once with LLM_PROVIDER=azure on this state, see team/PLAN.md P-49).
"""
import json
import re
import sys
from collections import Counter

from fastapi.testclient import TestClient

from app.core import config
from app.main import app
from app.modules.catalog import service as catalog
from app.modules.ingestion import service as ingestion
from app.modules.workpackages import service as workpackages

OPP = "OPP-0003"
ACCOUNTS = {(a["bu"], a["role"]): a["username"] for a in json.loads((config.DATA / "accounts.json").read_text("utf-8"))}
BM, PM, DE = "bid_manager", "product_manager", "design_engineer"
OFFERED = ("FPM", "ANORD", "CROWN", "CLOUD", "EP2", "JETCOOL", "EMS")  # the units with work in RC-1; EPC is not offered

# A capability gap: (what the customer reads: the gap's response in the compliance matrix, the internal rationale: the
# comment on the requirement, for the bid team only); its reason, also in the customer's matrix, is GAP_REASON.
GAP_REASON = "Outside the scope offered in this tender."
POWER_BLOCK = ("Not offered in this tender: the power blocks that convert MV AC to 800 VDC (about 5 MW each, Lot 2). The "
               "offer connects to their 800 VDC output.",
               "Power blocks are EPC Power's scope; EPC Power is not offered until its acquisition closes, and no other "
               "Flex unit makes MW-scale power blocks.")
HV_WHY = "Outside the Flex portfolio: Anord Mardix packaged substations go up to 33 kV on the primary side."
HV = ("Not offered in this tender: a service substation above 100 kV (utility line landing and HV-to-13.8 kV "
      "transformers). The offer starts at the 13.8 kV MV switchgear.", HV_WHY)
HV_L1 = ("Not offered in this tender: L1.01, the service substation above 100 kV (utility line landing and HV-to-13.8 kV "
         "transformers). L1.02 and L1.03 (two 13.8 kV MV buses, generation and storage on the MV bus) are answered with "
         "the MV switchgear lineups in REQ-0003-0211 and REQ-0003-0049.", HV_WHY)
PLANT = ("Not offered in this tender: the facility heat-rejection plant (dry coolers, chillers, pumps, room air handlers "
         "and outdoor prefabricated cooling). The offer covers the liquid cooling from the CDUs to the cold plates.",
         "Not in the Flex cooling portfolio; JetCool covers the loop from the CDU to the cold plates.")

# (kind, req_id, quote the item must hold now, fields, reason). "add": req_id None, the quote is what the lines hold.
CORRECTIONS = [
    ("add", None, "tolerate any disturbance",
     {"page": 6, "line_start": 35, "line_end": 36, "category": "technical",
      "text": "Each lot's equipment shall tolerate any disturbance foreseeable within the Section 9 interface limits."},
     "Missed by the reader: the closing sentence of the Section 9 introduction is a mandatory requirement on every lot."),
    ("edit", "REQ-0003-0060", "high-frequency sensing at the",
     {"text": "Series arcing shall be mitigated with connector temperature monitoring and high-frequency sensing at the "
              "rack interface and at converter outputs."},
     "L3.11 continues on page 4 ('rack interface and at converter outputs'); the reading stopped at the page break."),
    ("edit", "REQ-0003-0144", "spares and five years",
     {"text": "The price schedule shall separate equipment, freight, installation, commissioning, spares and five years "
              "of maintenance, with any extension beyond five years priced as an option."},
     "CT-02 continues on page 8 ('of maintenance, with any extension beyond five years priced as an option'); the "
     "reading stopped at the page break."),
    ("edit", "REQ-0003-0237", "Tenders are scored on technical value", {"category": "submission"},
     "Section 13 introduction and EV-02 to EV-04 say how the Owner scores tenders: evaluation rules for the bid desk, "
     "not a compliance item of a unit."),
    ("edit", "REQ-0003-0238", "Award goes to the tender", {"category": "submission"},
     "EV-01, EV-05, EV-10 and EV-11 are the Owner's award and responsiveness rules: evaluation rules for the bid desk, "
     "not a compliance item of a unit."),
    ("edit", "REQ-0003-0184", "RF-05", {"category": "submission"},
     "RF-05 (single point of contact) is a rule of the tender procedure, answered once by the bid desk."),
    ("edit", "REQ-0003-0155", "sanctions", {"category": "legal"},
     "CT-13 (sanctioned entities) is a legal eligibility condition, not a product standard."),
    ("edit", "REQ-0003-0004", "PM-03", {"category": "submission"},
     "PM-03 states who owns the campus design (the Owner's consultant): procurement information for the bid desk, "
     "not a compliance item."),
    ("edit", "REQ-0003-0016", "DB-11", {"category": "legal"},
     "DB-11 is an Owner obligation (interconnection agreements and permits): a legal statement, not a product item."),
    ("edit", "REQ-0003-0164", "ISO 9001", {"category": "submission"},
     "Company certifications (ISO 9001, 27001, 14001, 45001) are a qualification statement made once for the bid, "
     "not a product standard."),
    ("edit", "REQ-0003-0236", "Warranty is included", {"category": "commercial"},
     "CT-09 (warranty) and CT-10 (responsibility for foreseeable disturbances) are commercial and liability terms, "
     "not technical specifications; each unit's manager states its warranty terms."),
    ("edit", "REQ-0003-0153", "supply-chain security", {"category": "commercial"},
     "CT-11 (supply-chain security guarantee for the system's lifetime, with a risk plan) is a commercial commitment "
     "each unit's manager makes, not a technical specification."),
    ("edit", "REQ-0003-0112", "L6.17", {"category": "technical"},
     "L6.17 asks the bidder to run named AI benchmarks on the offered system: a technical requirement, not a "
     "submission formality."),
    ("edit", "REQ-0003-0105", "L6.10", {"category": "technical"},
     "L6.10 (system availability, mean time between interrupts) is a technical performance commitment."),
    ("edit", "REQ-0003-0048", "product maturity", {"category": "technical"},
     "L2.19 asks for product maturity, field references and type-test evidence for the offered power-block input "
     "class: technical evidence on the product."),
    ("edit", "REQ-0003-0111", "L6.16", {"category": "technical"},
     "L6.16 (on-site parts cache and spare nodes) is a technical support requirement on the compute system, not staffing."),
    ("edit", "REQ-0003-0037", "dynamic regulation",
     {"text": "Output shall be 800 VDC nominal, unipolar, with ripple ±0.5%, static regulation ±1% and dynamic regulation "
              "±3%. Sources shall not produce 800 VDC plus 10%, and setpoints shall stay below 1500 VDC."},
     "L2.09 continues on page 3 ('±3%. Sources shall not produce 800 VDC plus 10%, and setpoints shall stay below 1500 "
     "VDC'); the reading stopped at the page break and put the tail in REQ-0003-0215 as REQ-0003-0038."),
    ("exclude", "REQ-0003-0038", "Sources shall not produce 800 VDC plus 10%", {},
     "The tail of L2.09 (the power-block output), cut at the page break: L2.09 is now complete in REQ-0003-0037; the "
     "tail is not part of the voltage and grounding group, which starts at L2.10."),
    ("edit", "REQ-0003-0079", "UL 62368-1",
     {"text": "Rack power equipment shall use UL 62368-1 methods, with leakage of at most 3.5 mA AC and 10 mA DC, and "
              "shall meet EMC Class A to CISPR 32 and 35."},
     "L4.11 continues on page 5 ('and shall meet EMC Class A to CISPR 32 and 35'); the reading stopped at the page break "
     "and made the tail a requirement of its own (REQ-0003-0080)."),
    ("exclude", "REQ-0003-0080", "CISPR 32", {},
     "The tail of L4.11, cut at the page break: L4.11 is now complete in REQ-0003-0079 (group REQ-0003-0222)."),
    ("edit", "REQ-0003-0122", "IF-09",
     {"text": "Lots 2, 3 and 5 to Lot 6: telemetry and control over Modbus TCP/IP from power blocks and Redfish, PMBus, "
              "Modbus or CANbus elsewhere, integrated with the Owner's electrical power management system."},
     "IF-09 continues on page 7 ('PMBus, Modbus or CANbus elsewhere, integrated with the Owner's electrical power "
     "management system'); the reading stopped at the page break and made the tail a requirement of its own "
     "(REQ-0003-0123)."),
    ("exclude", "REQ-0003-0123", "PMBus, Modbus or CANbus elsewhere", {},
     "The tail of IF-09, cut at the page break: IF-09 is now complete in REQ-0003-0122 (interface group REQ-0003-0230)."),
    ("edit", "REQ-0003-0166", "Tier Designer", {"category": "submission"},
     "BQ-09 (an in-house Uptime-accredited Tier Designer is preferred) is a qualification preference stated once for "
     "the whole bid, like the company certifications (BQ-07): the bid desk answers it, not each unit."),
]

# The final solution of each item whose match was wrong or missing: req_id (or "ADDED" for the added sentence) ->
# (quote it must hold, [(product, type of offer)] main unit first, or GAP, reason for the change; for a GAP the reason
# is (customer-facing text, internal rationale), see POWER_BLOCK).
GAP = "gap"
SOLUTIONS = {
    "REQ-0003-0209": ("DB-06", [("ANORD-POD", "SEMI_CUSTOM"), ("JETCOOL-CDU", "SEMI_CUSTOM")],
                      "Design basis for the whole campus (availability, redundancy, cooling water, ambient and outdoor "
                      "ratings), not a Crown switchgear item: the power distribution and cooling teams design to it."),
    "REQ-0003-0228": ("L6.05", [("CLOUD-INT", "SEMI_CUSTOM")],
                      "Power controls from system to component level, load warnings and sequenced power up are "
                      "compute-system functions (Lot 6): Cloud rack-scale integration, not the FPM DC PDU."),
    "REQ-0003-0220": ("800 VDC to 54 VDC power shelf", [("FPM-800V", "SEMI_CUSTOM")],
                      "An 800 to 54 VDC in-rack power shelf belongs to the FPM 800 VDC module family, not the in-row DC PDU."),
    "REQ-0003-0230": ("IF-02", [("CLOUD-INT", "SEMI_CUSTOM"), ("CROWN-ARMV", "ETO"), ("ANORD-BUSWAY", "CTO"),
                                ("FPM-800V", "CTO"), ("JETCOOL-CDU", "SEMI_CUSTOM")],
                      "The interface schedule spans every lot, not only busway: each team confirms its own handoff and "
                      "Cloud integrates them."),
    "REQ-0003-0064": ("Facility storage", GAP,
                      ("Not offered in this tender: campus energy storage at the MV bus or the 800 VDC backbone. Rack-level "
                       "capacitive storage is offered with the rack power shelves.",
                       "Campus storage at the MV bus or the 800 VDC backbone is EPC Power's scope (storage conversion); EPC "
                       "Power is not offered until its acquisition closes. FPM capacitive storage is rack-level only.")),
    "REQ-0003-0040": ("Overload shall be 150%", GAP, POWER_BLOCK),
    "REQ-0003-0041": ("Efficiency shall be at least 98%", GAP, POWER_BLOCK),
    "REQ-0003-0044": ("state machine", GAP, POWER_BLOCK),
    "REQ-0003-0046": ("sub-blocks", GAP, POWER_BLOCK),
    "REQ-0003-0213": ("power blocks that convert MV AC to 800 VDC", GAP, POWER_BLOCK),
    "REQ-0003-0043": ("Outdoor enclosures shall be NEMA 3R", GAP, POWER_BLOCK),
    "REQ-0003-0045": ("Auxiliary power shall come from 480 Vac", GAP, POWER_BLOCK),
    "REQ-0003-0047": ("UL 347A", GAP, POWER_BLOCK),
    "REQ-0003-0048": ("product maturity", GAP, POWER_BLOCK),
    "REQ-0003-0210": ("above 100 kV", GAP, HV_L1),
    "REQ-0003-0114": ("IF-01", GAP, HV),
    "REQ-0003-0027": ("Backup generation", GAP,
                      ("Not offered in this tender: standby generation (central or prefabricated generators and their fuel "
                       "autonomy).",
                       "Standby generation is not in the Flex portfolio; a partner or another lot would supply it.")),
    "REQ-0003-0224": ("dry coolers", GAP, PLANT),
    "REQ-0003-0083": ("Central utility buildings", GAP, PLANT),
    "REQ-0003-0225": ("Room air handlers", GAP, PLANT),
    "REQ-0003-0095": ("Prefabricated cooling equipment", GAP, PLANT),
    "REQ-0003-0109": ("Slurm and Kubernetes", GAP,
                      ("Not offered in this tender: the cluster software and cloud services (Slurm, Kubernetes with GPU "
                       "passthrough, self-service portal, accounting). The offer covers the compute hardware and its "
                       "integration.",
                       "Cluster software is not a Flex product; Flex integrates the hardware and a software partner would "
                       "supply the stack.")),
    "REQ-0003-0028": ("protection-coordination data", [("EP2-RPP", "ETO")],
                      "Protection-coordination data comes with the relay and protection panels."),
    "REQ-0003-0214": ("Short-circuit withstand", [("CROWN-ARMV", "ETO")],
                      "Short-circuit withstand and basic impulse level at 13.8 kV are MV switchgear ratings, as in "
                      "REQ-0003-0211."),
    "REQ-0003-0223": ("serves GPU cold plates", [("JETCOOL-CDU", "SEMI_CUSTOM"), ("JETCOOL-PLATE", "CTO")],
                      "The CDU secondary loop serves the GPU cold plates: JetCool direct-to-chip cold plates go with the "
                      "CDUs (racks of about 570 kW, REQ-0003-0220, need direct-to-chip cooling: rule R-002)."),
    "REQ-0003-0084": ("facility water up to 45", [("JETCOOL-CDU", "SEMI_CUSTOM")],
                      "Facility water up to 45 °C is the CDU primary-side design point."),
    "REQ-0003-0227": ("measured per node and per loop", [("JETCOOL-CDU", "SEMI_CUSTOM")],
                      "Cooling measurement per loop and the piping and floor loading per hall come with the CDU and "
                      "manifold design."),
    "REQ-0003-0090": ("ASHRAE A2", [("JETCOOL-HYBRID", "SEMI_CUSTOM")],
                      "Air-cooled equipment and auxiliary racks above 20 kW: liquid-assisted air cooling."),
    "REQ-0003-0091": ("thermal ride-through", [("JETCOOL-CDU", "SEMI_CUSTOM")],
                      "Thermal ride-through and the restart sequence of the GPU-side loop are CDU behaviour."),
    "REQ-0003-0092": ("chemical management plan", [("JETCOOL-CDU", "SEMI_CUSTOM")],
                      "Coolant additives and handling are part of the CDU secondary loop supply."),
    "REQ-0003-0067": ("system-level simulation", [("EMS-TEST", "ETO")],
                      "System-level simulation and fault studies: the same scope as TA-07 (REQ-0003-0131), answered "
                      "by one team."),
    "REQ-0003-0231": ("TA-01", [("EMS-TEST", "ETO")],
                      "Factory, pre-delivery and power-chain tests: Flex test and validation services."),
    "REQ-0003-0222": ("UL 9540", [("FPM-SHELF", "CTO")],
                      "Rack power equipment standards (UL 62368-1, leakage) apply to the rack power shelves; the "
                      "storage standards are answered against the rack-level storage only."),
    "REQ-0003-0099": ("shall not exceed 20 MW", [("CLOUD-INT", "SEMI_CUSTOM")],
                      "The power drawn by each deployment unit under any workload is a compute-system figure."),
    "REQ-0003-0106": ("ISO/IEC 27001", [("CLOUD-INT", "SEMI_CUSTOM")],
                      "Tenant isolation and patching of firmware and drivers apply to the integrated compute system."),
    "REQ-0003-0107": ("POSIX parallel file system", [("CLOUD-TRAY", "SEMI_CUSTOM")],
                      "Multi-tier storage hardware: compute and storage joint design and build."),
    "REQ-0003-0108": ("control-plane network", [("CLOUD-INT", "SEMI_CUSTOM")],
                      "The control-plane network is part of the integrated compute system."),
    "REQ-0003-0129": ("TA-05", [("CLOUD-INT", "SEMI_CUSTOM")],
                      "The availability test rules apply to the integrated compute system."),
    "REQ-0003-0175": ("energy-to-solution", [("CLOUD-INT", "SEMI_CUSTOM")],
                      "Energy-to-solution and time-to-solution on the Owner's workload are compute-system commitments."),
    "REQ-0003-0112": ("L6.17", [("CLOUD-INT", "SEMI_CUSTOM")], "The AI benchmarks run on the integrated compute system."),
    "REQ-0003-0111": ("L6.16", [("CLOUD-INT", "SEMI_CUSTOM")],
                      "On-site parts cache and spare nodes for the compute system: the Cloud team holds the compute "
                      "spares, and the aftermarket unit does not take part in this bid."),
    "ADDED": ("tolerate any disturbance", [("CROWN-ARMV", "ETO"), ("ANORD-BUSWAY", "CTO"), ("FPM-800V", "CTO"),
                                           ("JETCOOL-CDU", "SEMI_CUSTOM"), ("CLOUD-INT", "SEMI_CUSTOM")],
              "Applies to every lot's equipment at its interface: each power, cooling and compute team confirms it."),
}
PRODUCT_CATEGORIES = {"technical", "compliance"}  # = matching.PRODUCT_CATEGORIES: the engineers' items
# The RFP due date the bid manager enters: RC-1 is issued 13 Oct 2026 (p. 1) and its schedule chart (Section 14, an image
# the reader does not read: "weeks from issue") gives qualification 7 weeks, so the first response is due 1 Dec 2026;
# the final tender follows after the dialogue, at about week 35.
DUE_DATE = "2026-12-01"


class Api:
    """The real API, signed in as the demo accounts (one token each)."""

    def __init__(self):
        if not config.DEMO_PASSWORD:
            sys.exit("Set DEMO_PASSWORD in .env: the demo accounts sign in with it.")
        self.client, self.tokens = TestClient(app), {}

    def __call__(self, who: str, method: str, path: str, body: dict | None = None):
        if who not in self.tokens:
            r = self.client.post("/api/auth/login", json={"username": who, "password": config.DEMO_PASSWORD})
            assert r.status_code == 200, f"sign-in {who}: {r.status_code} {r.text}"
            self.tokens[who] = {"Authorization": f"Bearer {r.json()['token']}"}
        r = self.client.request(method, f"/api{path}", json=body, headers=self.tokens[who])
        assert r.status_code < 300, f"{who} {method} {path}: {r.status_code} {r.text}"
        return r.json()


def user(bu: str | None, role: str) -> str:
    return ACCOUNTS[(bu, role)]


def bu_of(product_id: str) -> str:
    return catalog.product(product_id)["bu"]


def rows(api: Api) -> dict[str, dict]:
    return {r["req"]["req_id"]: r for r in api(user(None, BM), "GET", f"/bids/{OPP}/trace")["rows"]}


def holds(row: dict, fragment: str) -> bool:
    return fragment.lower() in (row["req"]["quote"] + " " + " ".join(k["text"] for k in row["children"])).lower()


def correct(api: Api) -> tuple[int, str | None]:
    """Step 1: the bid manager's corrections of the reading. Returns (how many, the added requirement's ID)."""
    live, made, added = rows(api), 0, None
    kids = {k["req_id"]: (r, k) for r in live.values() for k in r["children"]}  # sub-requirements (L6.10, L3.11, CT-02)
    for kind, req_id, fragment, fields, reason in CORRECTIONS:
        if kind == "add":
            if any(holds(r, fragment) for r in live.values()):
                print(f"  skip add: '{fragment}' is in the register already")
                continue
            out = api(user(None, BM), "POST", f"/bids/{OPP}/corrections", {"kind": "add", "reason": reason, **fields})
            added = out["added"][0]
        else:
            r = live.get(req_id) or kids.get(req_id, (None, None))[0]
            if kind == "exclude" and not r:
                print(f"  skip {req_id}: already excluded")
                continue
            assert r and holds(r, fragment), f"{req_id} no longer holds '{fragment}': re-check the correction"
            current = r["req"] if req_id in live else None
            if kind == "edit" and current and all(current.get(k) == v for k, v in fields.items()):
                print(f"  skip {req_id}: already corrected")
                continue
            out = api(user(None, BM), "POST", f"/bids/{OPP}/corrections",
                      {"kind": kind, "req_id": req_id, "reason": reason, **fields})
        made += 1
        print(f"  {kind} {req_id or out['added']}: version {out['baseline']} {out['note']}".rstrip())
    return made, added


LIVE = {"on": False}   # --live-new-steps: the new steps (addendum, configurator) may call the model once


class live:
    """Inside the block the model gateway may call Azure (when --live-new-steps is given); outside it, mock."""
    def __enter__(self):
        self.was = config.LLM_PROVIDER
        if LIVE["on"]:
            config.LLM_PROVIDER = "azure"

    def __exit__(self, *exc):
        config.LLM_PROVIDER = self.was


def add_addendum(api: Api) -> dict:
    """Step 1b (P-59): the synthetic Addendum No. 1 as a change document: read, every classification confirmed, applied."""
    bm = user(None, BM)
    if any(holds(r, "L4.13") for r in rows(api).values()):
        print("  skip: the addendum is applied already")
        return {}
    s = api(bm, "POST", f"/bids/{OPP}/changes/from-sample", {"name": "rc1_addendum_1"})
    api(bm, "POST", f"/changes/{s['id']}/confirm-all")
    out = api(bm, "POST", f"/changes/{s['id']}/apply")
    result = out.get("result") or {}
    print(f"  applied: version {result.get('baseline')}, added {result.get('added')}, modified {result.get('modified')}")
    return {k: result.get(k) for k in ("baseline", "added", "modified", "removed")}


def publish_product_documents(api: Api) -> int:
    """Step 4 (P-58): each supplied product document is published by the manager of the unit its families belong to."""
    unit_of = {d["title"]: next((catalog.product(k.split("/", 1)[0]) or {}).get("bu") for k in d["family_keys"])
               for d in catalog.documents()}
    n = 0
    for s in api(user(None, BM), "GET", "/knowledge/sources?collection=product_evidence")["sources"]:
        if s["status"] != "draft" or not unit_of.get(s["title"]):
            continue
        api(user(unit_of[s["title"]], PM), "POST", f"/knowledge/sources/{s['ks_id']}/review", {"approve": True, "note": (
            "Illustrative: the unit's own published datasheet or brochure, supplied for the PoC; accepted as product "
            "evidence. Its ratings stay unverified in the spec tables until the unit confirms them.")})
        n += 1
    return n


def comment(api: Api, who: str, req_id: str, text: str) -> None:
    api(who, "POST", f"/bids/{OPP}/comments", {"req_id": req_id, "text": text, "kind": "comment"})


def review_matches(api: Api, solutions: dict) -> Counter:
    """Step 2: each unit's designer / engineer confirms the technical matches that are right and corrects the others."""
    done = Counter()
    for req_id, r in rows(api).items():
        m = r["match"]
        if r["req"]["category"] not in PRODUCT_CATEGORIES or not m or not m["units"]:
            continue
        engineer = user(m["units"][0]["bu"], DE)  # the main unit's designer / engineer
        if req_id not in solutions:
            if m["status"] != "accepted":
                api(engineer, "POST", f"/matches/{m['id']}/decide", {"action": "accept"})
                done[(m["units"][0]["bu"], "confirmed")] += 1
            continue
        fragment, want, why = solutions[req_id]
        assert holds(r, fragment), f"{req_id} no longer holds '{fragment}': re-check its solution"
        units = [] if want == GAP else [{"product_id": p, "offering_type": t} for p, t in want]
        if [(u["product_id"], u["offering_type"]) for u in m["units"]] == ([] if want == GAP else list(want)):
            continue
        if want != GAP and m["units"][0]["bu"] != bu_of(want[0][0]):
            units = []  # another unit's item: no unit here, the bid manager routes it (step 3)
        api(engineer, "POST", f"/bids/{OPP}/requirements/{req_id}/match", {"units": units})
        name = catalog.unit(m["units"][0]["bu"])["name"]
        comment(api, engineer, req_id, f"Match corrected: {why}" if units else f"Not offered by {name}: {why[1]}" if want == GAP
                else f"Moved from {name} to {', '.join(dict.fromkeys(catalog.unit(bu_of(p))['name'] for p, _ in want))}: {why}")
        done[(m["units"][0]["bu"], "corrected")] += 1
    return done


def route_and_send(api: Api, solutions: dict) -> dict:
    """Step 3: the bid manager's first stage (C-41, P-44): business relevance, participation, routing, gaps, dispatch."""
    bm, out = user(None, BM), {"routed": 0, "gaps": 0}
    a = api(bm, "GET", f"/bids/{OPP}/assessment")
    print(f"  assessment: {a['summary']['requirements']} requirements, by category {a['summary']['by_category']}, "
          f"suggested units {sorted(a['summary']['suggested_units'])}")
    api(bm, "PUT", f"/bids/{OPP}/schedule", {"due_date": DUE_DATE, "consolidation_days": 5})
    api(bm, "POST", f"/bids/{OPP}/participation", {"units": list(OFFERED), "rationale": (
        "RC-1 is a cloud and power bid: Flex Power Modules, Anord Mardix, Crown, EP², JetCool, Cloud and the "
        "test services hold work. EPC Power is not offered until its acquisition closes, so the 800 VDC power blocks "
        "and campus storage are capability gaps, as are the HV substation, standby generation, the heat-rejection "
        "plant and the cluster software; the civil works of the MV feeders (L1.07) are not offered.")})
    for req_id, r in rows(api).items():
        m = r["match"]
        if r["req"]["category"] not in PRODUCT_CATEGORIES or (m and m["units"]):
            continue
        assert req_id in solutions, f"{req_id} has no unit and no decision in SOLUTIONS: {r['req']['text']}"
        fragment, want, why = solutions[req_id]
        assert holds(r, fragment), f"{req_id} no longer holds '{fragment}'"
        if want == GAP:
            continue  # after routing: a gap needs the participation and no unit holding it
        bus = list(dict.fromkeys(bu_of(p) for p, _ in want))
        api(bm, "POST", f"/bids/{OPP}/requirements/{req_id}/route", {"units": bus})
        comment(api, bm, req_id, f"Routed to {', '.join(bus)}: {why}")
        engineer = user(bus[0], DE)  # the receiving unit's designer / engineer confirms and sets the solution
        api(engineer, "POST", f"/bids/{OPP}/requirements/{req_id}/match",
            {"units": [{"product_id": p, "offering_type": t} for p, t in want]})
        out["routed"] += 1
    for item in api(bm, "GET", f"/bids/{OPP}/needs-owner"):
        fragment, want, (customer, internal) = solutions[item["req_id"]]
        assert want == GAP, f"{item['req_id']} still needs an owner"
        api(bm, "POST", f"/bids/{OPP}/requirements/{item['req_id']}/capability-gap",
            {"reason": GAP_REASON, "response": f"Illustrative placeholder response: {customer}"})
        comment(api, bm, item["req_id"], f"Capability gap recorded: {internal}")  # the bid team's own rationale
        out["gaps"] += 1
    sent = api(bm, "POST", f"/bids/{OPP}/dispatch")
    assert sent["needs_owner"] == 0, sent
    out["dispatched"] = sent["created"]
    return out


def part_a() -> dict:
    api = Api()
    assert api(user(None, BM), "GET", f"/bids/{OPP}")["opportunity"]["status"] == "frozen", \
        f"{OPP} is not the freshly seeded RC-1: run scripts.seed_demo --reset first"
    print("part A, step 1: corrections of the reading (bid manager)")
    made, added = correct(api)
    solutions = {(added if k == "ADDED" else k): v for k, v in SOLUTIONS.items() if k != "ADDED" or added}
    print("part A, step 1b: the bid manager applies the synthetic Addendum No. 1 (L4.13 to L4.15)")
    with live():
        addendum = add_addendum(api)
    print("part A, step 2: the units' designers / engineers review the technical matches")
    reviewed = review_matches(api, solutions)
    print("part A, step 3: the bid manager's first stage")
    sent = route_and_send(api, solutions)
    print("part A, step 4: product documents published by the unit managers; the bid manager runs the configurator")
    published = publish_product_documents(api)
    with live():
        components = api(user(None, BM), "POST", f"/bids/{OPP}/components")
    summary = {"corrections": made, "added": added, "addendum": addendum,
               "reviewed": {f"{bu} {k}": n for (bu, k), n in sorted(reviewed.items())}, **sent,
               "work": assignments(api)["counts"], "product_documents_published": published,
               "components": dict(Counter(c["outcome"] for c in components["components"]))}
    print("part A:", json.dumps(summary, indent=1))
    return summary


RFP_ID = re.compile(r"^((?:L\d\.\d{2}|[A-Z]{2}-\d{2}))\b")
SOURCE = re.compile(r"p\. (\d+), lines? (\d+)")


def assignments(api: Api) -> dict:
    """Every dispatched assignment: who answers it, the requirement's full text and the proposed solution."""
    trace = api(user(None, BM), "GET", f"/bids/{OPP}/trace")
    lines = {p["page"]: p["lines"] for p in ingestion.layout(trace["doc"]["id"])["pages"]}

    def rfp_ids(r):  # the RFP's own IDs: the first table cell of the first line of the item (of each part of a group)
        starts = [(int(p), int(n)) for k in r["children"] for p, n in SOURCE.findall(k["source"])[:1]] \
            or [(r["req"]["page"], r["req"]["line_start"])]
        ids = [m.group(1) for p, n in starts if p and n and (m := RFP_ID.match(lines[p][n - 1]["text"]))]
        return list(dict.fromkeys(ids))

    wf, units, desk = workpackages.workflow(), [], []
    for r in trace["rows"]:
        req, m = r["req"], r["match"] or {}
        for a in r["assignments"]:
            kind = "BID" if a["bu"] == "BID" else ("technical" if req["category"] in PRODUCT_CATEGORIES else "non_technical")
            entry = {"assignment_id": a["id"], "req_id": req["req_id"], "unit": a["bu"], "role": wf["respond"][kind][0],
                     "validator": wf["validate"][kind][0],
                     "category": req["category"], "summary": req["text"], "text": req["quote"],  # verbatim, a group's parts joined
                     "parts": [{"req_id": k["req_id"], "text": k["text"]} for k in r["children"]],
                     "status": a["status"], "capability_gap": a["bu"] == "BID" and r["req"]["category"] in PRODUCT_CATEGORIES,
                     "rfp_id": ", ".join(rfp_ids(r)) or None}
            if a["bu"] != "BID":
                ref = next((u["product_id"] for u in m.get("units", []) if u["bu"] == a["bu"]), a["product_ref"])
                entry["proposed_solution"] = catalog.solution(a["bu"], ref) if ref else None
            (desk if a["bu"] == "BID" else units).append(entry)
    counts = Counter(f"{e['unit']} {e['role']}" for e in units + desk)
    return {"counts": dict(sorted(counts.items())), "assignments": units, "bid_desk": desk}


def person(bu: str, role: str) -> str:
    return user(None if role == BM else bu, role)  # the bid manager is no unit's person


# The one answer the bid manager returns with a question, and the unit manager's second answer (shows that path once).
RETURNED = ("JETCOOL", "REQ-0003-0233",
            "CT-03 and CT-08 say a conditional price or commercial exception can make the tender non-responsive. Can the "
            "base price stay firm for every phase, with the metals adjustment offered only as an alternative?",
            {"compliance": "met",
             "response": "Illustrative placeholder response: Our prices are in US dollars, free of taxes, and firm for every "
                         "phase; they cover delivery to site, installation, commissioning and training, and the price "
                         "schedule separates equipment, freight, installation, commissioning, spares and five years of "
                         "maintenance, with any extension priced as an option. A metals-indexed price for phases delivered "
                         "more than 18 months after award is offered only as an alternative in the commercial exceptions "
                         "schedule, for the Owner to choose or ignore.",
             "reason": "", "conditions": "", "workaround": "",
             "next_steps": "Price the firm-price risk premium for later phases before the commercial review."})
NOT_OFFERED = ("the EPC Power power blocks and campus storage, the HV substation above 100 kV, standby generation, the "
               "heat-rejection plant, the cluster software and the civil works of the MV feeders (L1.07)")
# The bid manager's own judgement of each criterion the system does not suggest as met (checked against the RFP), and
# a note on a suggested one; the others are recorded as suggested, with the system's detail as the note. A criterion
# not met and not here stops the run.
JUDGED = {"compliance": ("met", "Below the illustrative threshold only through the capability gaps, each stated in the "
                                f"response as not offered: {NOT_OFFERED}. Over the scope Flex offers, no product "
                                "requirement is non-compliant."),
          "pending_acquisition": ("met", "No answer depends on EPC Power. Its scope (the 800 VDC power blocks and the "
                                         "campus storage) is recorded as capability gaps and stated as not offered."),
          "scope_fit": ("met", "EMS is not a layer of the RFP but supplies the test and validation services the RFP asks "
                               "for across the lots (TA-01 to TA-07, REQ-0003-0231, REQ-0003-0131, REQ-0003-0067)."),
          "open_questions": ("met", "No open question and every source verified. Rule warnings checked: 800 VDC "
                                    "compatibility, the power-path answers of FPM, ANORD and CLOUD state 800 VDC products; "
                                    "utility-grade protection, the RFP states block redundancy with a catcher (DB-07), "
                                    "not 2N at utility level.")}
GO_RATIONALE = ("GO for Lot 4 in full, Lot 3 except the campus storage, the Lot 6 compute hardware and integration, and "
                "the Flex-made equipment of Lots 1, 2 and 5 (in Lot 2 the MV switchgear lineups, no power blocks): every "
                "item is answered and validated and the teams' estimates are accepted. Compliance is judged met: every "
                f"non-compliant product requirement is a capability gap, stated in the response as not offered: {NOT_OFFERED}. "
                "Outside the product scope one qualification item is non-compliant: no participating unit has the "
                "in-house Uptime-accredited Tier Designer that BQ-09 (REQ-0003-0166) prefers, a preference and not a "
                "minimum, so it does not stop the bid.")
RESPOND_FIELDS = ("compliance", "response", "reason", "conditions", "workaround", "next_steps")


def part_b(answers_dir=config.SEED / "rc1_answers") -> None:
    """P-49 second half: the placeholder answers, read from answers_dir/<UNIT>.json (BID.json: the bid desk).

    File format (one per unit, BID.json for the bid desk):
        {"_note": "ILLUSTRATIVE ...",
         "answers": [{"req_id": "REQ-0003-0211", "role": "design_engineer" | "product_manager" | "bid_manager",
                      "compliance": "met" | "partial" | "deviation" | "not_met",
                      "response": "Illustrative placeholder response: ...", "reason": "", "conditions": "",
                      "workaround": "", "next_steps": ""}, ...],
         "feasibility": {"estimate": "YYYY-MM-DD",          # unit files only: the unit manager's estimate
                         "factors": {"people": {"status": "ok" | "constraint", "note": ""}, "skills": {...},
                                     "capacity": {...}, "materials": {...}, "cost": {...}}}}
    reason is required for partial, deviation and not_met; workaround (the proposed change) for deviation. Each
    answer is given by the role named (the workflow's answering role); the unit managers enter the estimate and the
    five factors; the bid manager returns one answer with a question (RETURNED) and the unit answers again; every
    answer is validated by the workflow's validator; the bid manager accepts the teams' estimates, approves the
    compliance position and records the go/no-go with every criterion judged. The capability gaps were recorded in
    part A (validated non-compliant, with the reason) and are not answered again."""
    api, bm = Api(), user(None, BM)
    files = {p.stem: json.loads(p.read_text("utf-8")) for p in sorted(answers_dir.glob("*.json"))}
    work = assignments(api)
    entry = {(e["unit"], e["req_id"]): e for e in work["assignments"] + work["bid_desk"]}
    print("part B, step 1: the units' people and the bid desk answer their items")
    for bu, f in files.items():
        for a in f["answers"]:
            e = entry[(bu, a["req_id"])]
            assert e["role"] == a["role"] and e["status"] == "assigned", f"{bu} {a['req_id']}: {e['role']} {e['status']}"
            assert a["response"].startswith("Illustrative placeholder response:"), f"{bu} {a['req_id']}: not marked"
            api(person(bu, a["role"]), "POST", f"/assignments/{e['assignment_id']}/respond", {k: a[k] for k in RESPOND_FIELDS})
    answered = {(bu, a["req_id"]) for bu, f in files.items() for a in f["answers"]}
    left = [k for k, e in entry.items() if e["status"] == "assigned" and k not in answered]
    assert not left, f"assigned items without a placeholder answer: {left}"
    print("part B, step 2: the unit managers enter their delivery estimates and the five factors")
    for bu, f in files.items():
        if fe := f.get("feasibility"):
            api(user(bu, PM), "PUT", f"/bids/{OPP}/units/{bu}/completion", {
                "estimated_completion": fe["estimate"], "factors": [{"factor": k, **v} for k, v in fe["factors"].items()]})
    print("part B, step 3: the bid manager returns one answer with a question; the unit answers again")
    bu, req_id, question, again = RETURNED
    e = entry[(bu, req_id)]
    api(bm, "POST", f"/assignments/{e['assignment_id']}/validate", {"ok": False, "note": question})
    api(person(bu, e["role"]), "POST", f"/assignments/{e['assignment_id']}/respond", again)
    print("part B, step 4: every answer is validated by the workflow's validator")
    work = assignments(api)
    for e in work["assignments"] + work["bid_desk"]:
        if e["status"] == "submitted":
            api(person(e["unit"], e["validator"]), "POST", f"/assignments/{e['assignment_id']}/validate", {"ok": True})
    print("part B, step 5: the bid manager accepts the estimates, approves the compliance position, decides go")
    api(bm, "POST", f"/bids/{OPP}/approvals", {"kind": "schedule", "note": (
        "The teams' estimates and delivery factors are accepted; each constraint has a mitigation.")})
    api(bm, "POST", f"/bids/{OPP}/approvals", {"kind": "compliance", "note": (
        "The compliance position is approved as validated by the units, with the capability gaps stated.")})
    api(bm, "POST", f"/bids/{OPP}/reassessments", {"reason": (  # retrieval only: no model call
        "Knowledge-base assessment of the frozen register before the go/no-go, on the reviewed evidence published today.")})
    criteria = [{"id": c["id"], "status": c["status"], "note": c["detail"]} if c["status"] == "met" and c["id"] not in JUDGED
                else {"id": c["id"], "status": JUDGED[c["id"]][0], "note": JUDGED[c["id"]][1]}
                for c in api(bm, "GET", f"/bids/{OPP}/decisions")["summary"]["criteria"]]
    api(bm, "POST", f"/bids/{OPP}/go-no-go", {"outcome": "go", "rationale": GO_RATIONALE, "criteria": criteria})


def end_state(api: Api) -> dict:
    """The figures the demo shows at the end (the repeatability check compares them across fresh seeds)."""
    bm = user(None, BM)
    work = assignments(api)
    s = api(bm, "GET", f"/bids/{OPP}/schedule")
    gng = api(bm, "GET", f"/bids/{OPP}/decisions")["go_no_go"]
    matrix = api(bm, "GET", f"/bids/{OPP}/compliance-matrix")["rows"]
    outline = api(bm, "GET", f"/bids/{OPP}/response-outline")
    score = api(bm, "GET", f"/bids/{OPP}/assessment-score")
    sub = ("confirmed", "other_solution", "not_compliant_answer")
    product = api(bm, "GET", f"/bids/{OPP}/decisions")["summary"]["compliance"]
    trace = rows(api).values()
    return {
        "status": api(bm, "GET", f"/bids/{OPP}")["opportunity"]["status"],
        "assignments": dict(Counter(e["status"] for e in work["assignments"] + work["bid_desk"])),
        "needs_owner": len(api(bm, "GET", f"/bids/{OPP}/needs-owner")),
        "open_questions": sum(c["kind"] == "question" for c in api(bm, "GET", f"/bids/{OPP}/comments?status=open")),
        "measures": {k: f"{m['n']} of {m['of']}" + "".join(f", {s} {m[s]}" for s in sub if s in m)
                     for k, m in score["measures"].items()},
        "assessment_run": score["run"],
        "capability_gaps": outline["capability_gaps"],
        "proposed_product_matches": sum(bool(r["match"]) and r["match"]["status"] == "proposed"
                                        and r["req"]["category"] in PRODUCT_CATEGORIES for r in trace),
        "outcomes_per_product_requirement": {k: len(v) for k, v in product.items()},
        "outcomes": dict(Counter(r["compliance"] for r in matrix if r["unit"] and r["status"] == "validated")),
        "compliance_by_unit": s["compliance"],
        "feasibility": {u["bu"]: [u["estimated_completion"], u["constraints"]] for u in s["units"]},
        "planned_submission": s["planned_submission"],
        "approvals": {k: bool(a and a["current"]) for k, a in s["approvals"].items()},
        "go_no_go": [gng["outcome"], dict(Counter(c["status"] for c in gng["criteria"]))],
        "matrix_rows": len(matrix),
        "outline": {"validated_answers": outline["validated_answers"], "summary_drafted": outline["summary"]["drafted"],
                    "chapters": [[c["title"], c["total"], c["answered"], c["draft"]["drafted"]] for c in outline["chapters"]]},
    }


def main() -> dict:
    part_a()
    part_b()
    out = end_state(Api())
    print("end state:", json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    if "--dump" in sys.argv:  # only reads: the work as dispatched, for writing the placeholder answers
        path = sys.argv[sys.argv.index("--dump") + 1]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(assignments(Api()), f, indent=1, ensure_ascii=False)
        print("written:", path)
    else:
        LIVE["on"] = "--live-new-steps" in sys.argv
        main()
