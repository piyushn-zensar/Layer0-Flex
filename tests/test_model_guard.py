"""Model-change guard (P-09): the golden test over data/llm_cache, and the comparator checks on hand-made answers.

Run:  .venv\\Scripts\\python -m pytest -q tests/test_model_guard.py
The replay runs in its own process and temporary store (scripts/model_guard.py), so the opportunities it creates
never reach the other tests' database. MODEL_GUARD_REAL=1 also replays the full 348-requirement demo (reader and
grouping agents, about 1.5 min instead of 20 s).
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

os.environ["STORE_DIR"] = tempfile.mkdtemp()
os.environ["LLM_PROVIDER"] = "mock"

import pytest  # noqa: E402

from app.core import config, llm  # noqa: E402
from scripts import model_guard as guard  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REAL = os.getenv("MODEL_GUARD_REAL") == "1"


@pytest.fixture(scope="module")
def replay() -> dict:
    env = os.environ | {"LLM_PROVIDER": "mock", "PYTHONPATH": str(ROOT)}
    args = [sys.executable, "-m", "scripts.model_guard", "replay", "--json"] + (["--real"] if REAL else [])
    done = subprocess.run(args, cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", timeout=600)
    assert done.stdout.strip(), done.stderr[-3000:]
    return json.loads(done.stdout) | {"exit": done.returncode}


def test_demo_replays_from_frozen_answers(replay):
    """The golden test: a prompt or schema changed without regenerating its frozen answers fails here, by task."""
    missing = {task: t["misses"] for task, t in replay["tasks"].items() if t["misses"]}
    assert not missing, f"No frozen answer for these calls (regenerate them, never edit them): {missing}"
    assert not replay["listed_but_found"], "Frozen now: remove these from data/golden/model_guard_known_misses.json"
    assert replay["ok"] and replay["exit"] == 0


def test_recorder_sees_every_agent_of_the_demo(replay):
    called = {task for task, t in replay["tasks"].items() if t["calls"]}
    expected = {"match_requirement", "draft_outline", "read_changes", "classify_change"}
    assert expected | ({"read_requirements", "group_requirements"} if REAL else set()) <= called
    assert all(t["hits"] for task, t in replay["tasks"].items() if task in expected)


def test_frozen_answers_come_from_the_configured_model(replay):
    assert replay["model"] == config.LLM_MODEL
    assert not {task: t["wrong_model"] for task, t in replay["tasks"].items() if t["wrong_model"]}


def test_recorder_hook():
    """Collects every call inside the block (a miss too), and nothing outside it."""
    with llm.record() as calls:
        with pytest.raises(llm.LLMUnavailable):
            llm.complete_json("no_such_task", "system", "prompt", {"type": "object"})
    with pytest.raises(llm.LLMUnavailable):
        llm.complete_json("no_such_task", "system", "other prompt", {"type": "object"})
    assert [(c["task"], c["prompt"], c["hit"]) for c in calls] == [("no_such_task", "prompt", False)]
    assert len(calls[0]["key"]) == 24 and not llm._recorders


def test_recorder_nested_blocks():
    """Each block closes its own list, even when two open blocks hold equal (empty) lists."""
    with llm.record() as outer:
        with llm.record() as inner:
            pass
        with pytest.raises(llm.LLMUnavailable):
            llm.complete_json("no_such_task", "system", "prompt", {"type": "object"})
    assert (len(outer), len(inner)) == (1, 0) and not llm._recorders


def test_merged_quotes_count_once():
    """A new answer that merges several frozen quotes into one (or one word found in many) recalls only one."""
    item = lambda q: {"page": 1, "quote": q, "text": "", "category": "technical", "section": ""}
    qs = ["The switchgear shall be arc-resistant Type 2B.", "Provide two bus sections.", "Paint shall be ANSI 61."]
    old = {"requirements": [item(q) for q in qs]}
    assert guard.check_reader(old, {"requirements": [item(" ".join(qs))]}, "") == (1, 3)
    assert guard.check_reader(old, {"requirements": [item("shall")]}, "") == (1, 3)
    assert guard.check_reader(old, {"requirements": [item(q[:20]) for q in reversed(qs)]}, "") == (3, 3)  # cut short
    said = lambda q, action: {"page": 1, "quote": q, "text": "", "category": "commercial", "action": action}
    two = {"statements": [said("Bids are due 09/29/2023.", "modify"), said("Bid validity is 120 days.", "modify")]}
    merged = {"statements": [said("Bids are due 09/29/2023. Bid validity is 120 days.", "modify")]}
    assert guard.check_read_changes(two, merged, "") == (1, 2)


def test_compare_blocks_tasks_it_never_asked(monkeypatch, tmp_path):
    """Without --real the reader and grouping are never asked: no evidence, so no switch (stubbed model, no Azure)."""
    path = sorted((config.LLM_CACHE / "match_requirement").glob("*.json"))[0]
    call = {"task": "match_requirement", "system": "s", "prompt": "p", "schema": {}, "key": path.stem, "hit": True}
    monkeypatch.setattr(config, "LLM_PROVIDER", "azure")
    monkeypatch.setattr(guard, "replay", lambda real: ({"ok": True}, [call]))
    monkeypatch.setattr(llm, "_azure", lambda *args: guard.frozen("match_requirement", path.stem)["output"])
    r = guard.compare("gpt-next", False, tmp_path)
    assert r["tasks"]["match_requirement"]["ok"] and not r["ok"]
    assert {t for t, v in r["tasks"].items() if not v["ok"]} == set(guard.CHECKS) - {"match_requirement"}
    assert config.LLM_MODEL != "gpt-next" and (tmp_path / "report.json").exists()


def test_comparators_on_hand_made_answers():
    item = lambda q, page=1: {"page": page, "quote": q, "text": "", "category": "technical", "section": ""}
    old = {"requirements": [item("The switchgear shall be Arc-resistant Type 2B."), item("Provide two bus sections.")]}
    assert guard.check_reader(old, old, "") == (2, 2)
    reworded = {"requirements": [item("THE  switchgear shall be arc-resistant Type 2B")]}  # case, spaces, full stop
    assert guard.check_reader(old, reworded, "") == (1, 2)  # one quote missing: recall drops to 0.5

    unit = lambda bu, pid: {"bu": bu, "product_id": pid, "offering_type": "ETO"}
    match = {"answers": [{"n": 1, "units": [unit("CROWN", "CROWN-ARMV"), unit("EP2", "EP2-RPP")]},
                         {"n": 2, "units": []}]}
    assert guard.check_matcher(match, match, "") == (2, 2)
    other = {"answers": [{"n": 1, "units": [unit("EP2", "EP2-RPP")]}, {"n": 2, "units": []}]}
    assert guard.check_matcher(match, other, "") == (1, 2)  # a different main unit
    assert guard.check_matcher(match, {"answers": [match["answers"][0]]}, "") == (1, 2)  # no answer for n=2

    groups = {"groups": [{"title": "Drawings", "category": "submission", "members": [1, 2, 3]}]}
    assert guard.check_grouping(groups, groups, "") == (1, 1)
    assert guard.check_grouping(groups, {"groups": [{"title": "x", "category": "submission", "members": [1, 2]}]},
                                "") == (0, 1)
    assert guard.check_grouping({"groups": []}, {"groups": []}, "") == (1, 1)

    prompt = "CHAPTER: Technical\n\nVALIDATED ANSWERS\n[1] Crown | Comply\n[2] EP2 | Comply\n"
    draft = {"paragraphs": [{"text": "a", "cites": [1]}, {"text": "b", "cites": [1, 2]}], "gaps": []}
    assert guard.check_outline(draft, draft, prompt) == (2, 2)
    assert guard.check_outline(draft, {"paragraphs": [{"text": "a", "cites": [3]}, {"text": "b", "cites": []}],
                                       "gaps": []}, prompt) == (0, 2)
    assert guard.check_outline(draft, {"paragraphs": [], "gaps": []}, prompt) == (0, 1)

    said = lambda q, action: {"page": 1, "quote": q, "text": "", "category": "commercial", "action": action}
    read = {"statements": [said("Bids are due 09/29/2023.", "modify"), said("Acknowledge receipt.", "info")]}
    assert guard.check_read_changes(read, read, "") == (2, 2)
    assert guard.check_read_changes(read, {"statements": [said("Bids are due 09/29/2023.", "add")]}, "") == (0, 2)
    classified = {"answers": [{"n": 1, "change": "modified", "target": "A"}, {"n": 2, "change": "added", "target": ""}]}
    assert guard.check_classify(classified, classified, "") == (2, 2)
    assert guard.check_classify(classified, {"answers": [{"n": 1, "change": "modified", "target": "B"},
                                                         {"n": 2, "change": "added", "target": ""}]}, "") == (1, 2)

    assert guard.score("match_requirement", [(2, 2), (1, 1)])["ok"]
    low = guard.score("match_requirement", [(1, 2)])
    assert not low["ok"] and low["share"] == 0.5 and low["threshold"] == guard.MATCH_SAME


def test_compare_refuses_in_mock_mode(tmp_path):
    with pytest.raises(SystemExit, match="LLM_PROVIDER=azure"):
        guard.compare("gpt-next", False, tmp_path)
    assert not any(tmp_path.iterdir())
