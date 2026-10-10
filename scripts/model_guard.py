"""Model-change guard (P-09, ported from M16): the demo replays from frozen answers, and a new model must match them
before the switch.

    .venv\\Scripts\\python -m scripts.model_guard                  # replay: quick Syracuse, hyperscale, outline, addendum
    .venv\\Scripts\\python -m scripts.model_guard replay --real    # also the full 348-requirement demo (~3 min)
    .venv\\Scripts\\python -m scripts.model_guard replay --json    # the report as JSON on stdout (tests)
    (LLM_PROVIDER=azure) .venv\\Scripts\\python -m scripts.model_guard compare --model <new deployment> [--real] [--out DIR]

Every frozen answer is keyed by task, model, system prompt, prompt and schema (app/core/llm.py). So changing a prompt
or a schema without regenerating, or changing LLM_MODEL, leaves the demo without answers: in mock mode the agents
fall back or raise, quietly. This script makes that explicit and measurable.

replay (mock-safe, never calls a model): runs the demo pipelines in a temporary store with the gateway's recorder on,
and reports per task the calls, the frozen answers found, the misses (with their key), the frozen answers whose model
is not LLM_MODEL, and the cache files this replay never used (used by the tests, or stale: informational only).
Exit 1 on a miss or another model's answer. Today's gaps are listed, each with its reason, in
data/golden/model_guard_known_misses.json: reported as known, not failed (tests/test_model_guard.py is the gate).

compare (Azure only): replays the same calls, then asks the NEW model each recorded prompt and checks its answer
against the frozen one, per task (see CHECKS). The candidates go to a report folder outside the repo
(--out, default a new temporary folder); data/llm_cache is never written. Exit 1 when a task falls below its
threshold, or was not compared at all (without --real the reader and grouping are never asked: blocked). Do not
switch LLM_MODEL until it passes, and never edit a frozen answer to make it pass: regenerate the answers only after
a person has reviewed the differences.
"""
import argparse
import contextlib
import json
import os
import re
import sys
import tempfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

if __name__ == "__main__":
    os.environ["STORE_DIR"] = tempfile.mkdtemp(prefix="model_guard-")  # before app.core.config reads it

from app.core import config, llm  # noqa: E402
from app.modules.requirements.anchoring import normalise  # noqa: E402  (a pure helper, as in seed_demo)

BM = "Bid Manager"
ADDENDUM = config.ROOT / "data/RFP/samples/rfp_syracuse_addendum_1.pdf"
KNOWN_MISSES = config.ROOT / "data/golden/model_guard_known_misses.json"  # today's gaps, each with its reason

# Thresholds per task: starting guesses, to tune on the first real comparison (shares of items that agree).
READER_RECALL = 0.90    # frozen quotes the new model also returns
GROUPING_SAME = 0.70    # groups with the same members (grouping is a judgement call; people review it anyway)
MATCH_SAME = 0.85       # requirements with the same main unit and product
OUTLINE_VALID = 1.0     # paragraphs that cite only valid answer numbers (the guard drops the others)
CHANGE_SAME = 0.90      # statements with the same action, or the same change and target


# ---- replay ---------------------------------------------------------------------------------------------------

def run_demo(real: bool = False) -> None:
    """The demo pipelines, through the same services a user action calls (seed_demo plus the outline and addendum)."""
    from app.core.db import SessionLocal
    from app.modules.changes import service as changes
    from app.modules.consolidation import service as consolidation
    from app.modules.opportunities import service as opportunities
    from scripts import seed_demo

    def newest(seed_file: str = "demo_syracuse.json", real: bool = False) -> str:
        with SessionLocal() as db:
            before = {o.id for o in opportunities.list_all(db)}
        seed_demo.main(seed_file, real)
        with SessionLocal() as db:
            return next(o.id for o in opportunities.list_all(db) if o.id not in before)

    runs = [newest()] + ([newest(real=True)] if real else [])
    newest("demo_hyperscale.json")
    for opp in runs:
        with SessionLocal() as db:
            consolidation.response_outline(db, opp)
            try:
                s = changes.upload(db, opp, ADDENDUM.name, ADDENDUM.read_bytes(), BM)
            except ValueError as exc:  # no frozen answer: the misses are in the report
                print("addendum not read:", exc)
                continue
            changes.confirm_all(db, s.id, BM)
            print("addendum applied:", changes.apply(db, s.id, BM).result)


def replay(real: bool = False) -> tuple[dict, list[dict]]:
    """(report, recorded calls). Forces mock mode for the run: a miss is reported, never generated."""
    provider, config.LLM_PROVIDER = config.LLM_PROVIDER, "mock"
    try:
        with llm.record() as calls:
            run_demo(real)
    finally:
        config.LLM_PROVIDER = provider
    return report(calls), calls


def report(calls: list[dict]) -> dict:
    """{"model", "ok", "listed_but_found": [task/key], "tasks": {task: {"calls", "keys", "hits", "misses": [key],
    "known": [key], "wrong_model": [key], "unused": [key]}}}. known = misses listed in KNOWN_MISSES (reported, not
    failed); ok = no other miss and no frozen answer from another model. listed_but_found = KNOWN_MISSES entries
    that did not miss (remove them)."""
    listed = json.loads(KNOWN_MISSES.read_text("utf-8"))["misses"]
    tasks, missed = {}, set()
    names = sorted({c["task"] for c in calls} | {p.name for p in config.LLM_CACHE.iterdir() if p.is_dir()})
    for task in names:
        mine = [c for c in calls if c["task"] == task]
        keys = {c["key"] for c in mine}
        hits = sorted({c["key"] for c in mine if c["hit"]})
        misses = sorted(keys - set(hits))
        missed |= {f"{task}/{k}" for k in misses}
        files = {p.stem for p in (config.LLM_CACHE / task).glob("*.json")}
        tasks[task] = {
            "calls": len(mine), "keys": len(keys), "hits": len(hits),
            "misses": [k for k in misses if f"{task}/{k}" not in listed],
            "known": [k for k in misses if f"{task}/{k}" in listed],
            "wrong_model": [k for k in hits if frozen(task, k)["model"] != config.LLM_MODEL],
            "unused": sorted(files - keys),
        }
    ok = not any(t["misses"] or t["wrong_model"] for t in tasks.values())
    return {"model": config.LLM_MODEL, "ok": ok, "listed_but_found": sorted(set(listed) - missed), "tasks": tasks}


def frozen(task: str, key: str) -> dict:
    return json.loads((config.LLM_CACHE / task / f"{key}.json").read_text("utf-8"))


def print_report(r: dict) -> None:
    print(f"\nModel-change guard: replay with LLM_MODEL={r['model']}")
    print(f"  {'task':20} {'calls':>5} {'keys':>5} {'hits':>5} {'misses':>6} {'known':>5} {'unused':>6}")
    for task, t in r["tasks"].items():
        print(f"  {task:20} {t['calls']:5} {t['keys']:5} {t['hits']:5} {len(t['misses']):6} {len(t['known']):5}"
              f" {len(t['unused']):6}")
        for k in t["misses"]:
            print(f"      missing: {task}/{k}  (a prompt or schema changed without regenerating, or a new model)")
        for k in t["known"]:
            print(f"      known gap: {task}/{k}  (listed in {KNOWN_MISSES.relative_to(config.ROOT).as_posix()})")
        for k in t["wrong_model"]:
            print(f"      other model: {task}/{k}")
    for k in r["listed_but_found"]:
        print(f"  listed as a known gap but did not miss: {k} (frozen now, or no longer asked: remove it from the list)")
    print("  REPLAYS FROM FROZEN ANSWERS" if r["ok"] else "  MISSING FROZEN ANSWERS: the demo would need model calls")


# ---- compare: one check per task, each returns (items that agree, items) --------------------------------------

def quotes(items: list[dict]) -> list[str]:
    return [q for q in (normalise(i.get("quote", "")).rstrip(".;:, ") for i in items) if q]


def paired(old: list[str], new: list[str]) -> int:
    """Old quotes matched one to one with new ones (equal first, then one containing the other), so a new quote
    that merges several frozen ones, or a short one inside many, counts once."""
    free, left = list(new), []
    for q in old:
        if q in free:
            free.remove(q)
        else:
            left.append(q)
    same = len(old) - len(left)
    for q in left:
        n = next((n for n in free if q in n or n in q), None)
        if n is not None:
            free.remove(n)
            same += 1
    return same


def recall(frozen_items: list[dict], new_items: list[dict]) -> tuple[int, int]:
    """Frozen quotes the new answer also returns (equal, or one contains the other, after normalising; one to one)."""
    old = quotes(frozen_items)
    return paired(old, quotes(new_items)), len(old)


def check_reader(old: dict, new: dict, prompt: str) -> tuple[int, int]:
    return recall(old["requirements"], new["requirements"])


def check_grouping(old: dict, new: dict, prompt: str) -> tuple[int, int]:
    """Groups with exactly the same members, out of the larger number of groups (extra groups count against)."""
    a = [frozenset(g["members"]) for g in old["groups"]]
    b = {frozenset(g["members"]) for g in new["groups"]}
    total = max(len(a), len(b))
    return (sum(g in b for g in a), total) if total else (1, 1)


def main_unit(answer: dict) -> tuple | None:
    units = answer.get("units") or []
    return (units[0]["bu"], units[0]["product_id"]) if units else None


def check_matcher(old: dict, new: dict, prompt: str) -> tuple[int, int]:
    """Requirements with the same main unit and product (or both "not a product requirement")."""
    by_n = lambda out: {a["n"]: a for a in reversed(out["answers"])}  # the first answer for a number counts
    a, b = by_n(old), by_n(new)
    return sum(n in b and main_unit(a[n]) == main_unit(b[n]) for n in a), len(a)


def check_outline(old: dict, new: dict, prompt: str) -> tuple[int, int]:
    """Structure only: the new paragraphs cite at least one answer number, all of them in the prompt."""
    n_answers = len(re.findall(r"^\[\d+\] ", prompt, re.M))
    paragraphs = new["paragraphs"]
    if not paragraphs:
        return (1, 1) if not old["paragraphs"] else (0, 1)
    return sum(bool(p["cites"]) and all(1 <= c <= n_answers for c in p["cites"]) for p in paragraphs), len(paragraphs)


def check_read_changes(old: dict, new: dict, prompt: str) -> tuple[int, int]:
    """Frozen statements found again (by quote, one to one) with the same action."""
    by_action = lambda out, action: quotes([s for s in out["statements"] if s["action"] == action])
    actions = {s["action"] for s in old["statements"]}
    return (sum(paired(by_action(old, a), by_action(new, a)) for a in actions),
            len(quotes(old["statements"])))


def check_classify(old: dict, new: dict, prompt: str) -> tuple[int, int]:
    """Statements with the same change and the same target letter."""
    by_n = lambda out: {a["n"]: (a["change"], a["target"]) for a in reversed(out["answers"])}
    a, b = by_n(old), by_n(new)
    return sum(a[n] == b.get(n) for n in a), len(a)


CHECKS = {  # task: (check, threshold, what agrees)
    "read_requirements": (check_reader, READER_RECALL, "frozen quotes recalled"),
    "group_requirements": (check_grouping, GROUPING_SAME, "same group members"),
    "match_requirement": (check_matcher, MATCH_SAME, "same main unit and product"),
    "draft_outline": (check_outline, OUTLINE_VALID, "paragraphs with valid citations"),
    "read_changes": (check_read_changes, CHANGE_SAME, "same statement and action"),
    "classify_change": (check_classify, CHANGE_SAME, "same change and target"),
}


def score(task: str, results: list[tuple[int, int]]) -> dict:
    agree, total = sum(a for a, _ in results), sum(t for _, t in results)
    check, threshold, label = CHECKS[task]
    share = agree / total if total else 1.0
    return {"calls": len(results), "agree": agree, "total": total, "share": round(share, 3),
            "threshold": threshold, "what": label, "ok": share >= threshold}


def compare(model: str, real: bool, out: Path) -> dict:
    """Asks `model` every recorded prompt that has a frozen answer and scores it per task. Writes the candidates to
    out/<task>/<frozen key>.json and out/report.json; never to data/llm_cache."""
    if config.LLM_PROVIDER != "azure":
        raise SystemExit("compare asks a new model: set LLM_PROVIDER=azure (it never runs in mock mode).")
    if model == config.LLM_MODEL:
        raise SystemExit(f"--model {model} is the current model: name the new deployment.")
    replayed, calls = replay(real)
    unique = {c["key"]: c for c in calls if c["hit"] and c["task"] in CHECKS}.values()

    def ask(c: dict) -> tuple[str, tuple[int, int]]:
        old = frozen(c["task"], c["key"])["output"]
        try:
            new = llm._azure(c["task"], c["system"], c["prompt"], c["schema"])
        except Exception as exc:  # a refusal or an error counts as disagreement on every item
            new, result = {"error": str(exc)}, (0, max(CHECKS[c["task"]][0](old, old, c["prompt"])[1], 1))
        else:
            result = CHECKS[c["task"]][0](old, new, c["prompt"])
        path = out / c["task"] / f"{c['key']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"task": c["task"], "model": model, "frozen_key": c["key"], "agree": result,
                                    "output": new}, indent=2, ensure_ascii=False), "utf-8")
        return c["task"], result

    current, config.LLM_MODEL = config.LLM_MODEL, model  # _azure sends config.LLM_MODEL as the deployment
    try:
        with ThreadPoolExecutor(4) as pool:
            results = list(pool.map(ask, unique))
    finally:
        config.LLM_MODEL = current
    by_task = defaultdict(list)
    for task, result in results:
        by_task[task].append(result)
    tasks = {task: score(task, by_task[task]) for task in sorted(by_task)}
    for task in sorted(set(CHECKS) - set(by_task)):  # never asked (the reader and grouping run only with --real)
        tasks[task] = score(task, []) | {"share": 0.0, "ok": False, "what": "not compared: run with --real"}
    r = {"model": model, "baseline_model": current, "replay_ok": replayed["ok"], "out": str(out),
         "ok": all(t["ok"] for t in tasks.values()), "tasks": tasks}
    (out / "report.json").write_text(json.dumps(r, indent=2), "utf-8")
    return r


def print_compare(r: dict) -> None:
    print(f"\nModel-change guard: {r['model']} against the frozen answers of {r['baseline_model']}")
    print(f"  {'task':20} {'calls':>5} {'agree':>11} {'share':>6} {'needs':>6}  check")
    for task, t in r["tasks"].items():
        mark = "ok" if t["ok"] else "FAIL"
        print(f"  {task:20} {t['calls']:5} {t['agree']:5}/{t['total']:<5} {t['share']:6.2f} {t['threshold']:6.2f}"
              f"  {t['what']} {mark}")
    print(f"  candidates and report: {r['out']}")
    print("  SWITCH ALLOWED" if r["ok"] and r["replay_ok"] else
          "  SWITCH BLOCKED: review the differences; never edit a frozen answer to make it pass")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Model-change guard (P-09)")
    ap.add_argument("command", nargs="?", default="replay", choices=["replay", "compare"])
    ap.add_argument("--real", action="store_true", help="also the full 348-requirement Syracuse demo (~3 min)")
    ap.add_argument("--json", action="store_true", help="replay: print the report as JSON only")
    ap.add_argument("--model", help="compare: the new Azure deployment name")
    ap.add_argument("--out", type=Path, help="compare: report folder (default: a new temporary folder)")
    args = ap.parse_args(argv)
    if args.command == "compare":
        if not args.model:
            ap.error("compare needs --model <new deployment>")
        r = compare(args.model, args.real, args.out or Path(tempfile.mkdtemp(prefix="model_guard-compare-")))
        print_compare(r)
        return 0 if r["ok"] and r["replay_ok"] else 1
    with contextlib.redirect_stdout(sys.stderr) if args.json else contextlib.nullcontext():
        r, _ = replay(args.real)
    if args.json:
        print(json.dumps(r, indent=2))
    else:
        print_report(r)
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
