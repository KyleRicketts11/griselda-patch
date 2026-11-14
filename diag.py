#!/usr/bin/env python3
# diag.py - three-bucket failure triage for griselda's frozen eval set
# On a FAIL, diffs her action shape against the same task's last PASS:
#   TASK_STALE        frozen trace used an action that is no longer on her menu
#   MODEL_REGRESSION  identical action shape as the passing run, worse outcome
#   BEHAVIOR_CHANGED  she tried something different than last time, needs eyes
# read-only: reads eval_history.jsonl, writes nothing.
# usage: python diag.py
import json, os

BASE = os.environ.get("GRIS_BASE", os.path.expanduser("~/griselda-brain"))

def norm(x):
    # x is a stored result: prefer the full parsed action dict, fall back to got
    if isinstance(x, dict):
        a = str(x.get("action", "")).lower().strip()
        keys = tuple(sorted(k for k in x.keys() if k != "action"))
        vals = tuple(str(x.get(k, ""))[:60] for k in keys)
        return a, keys, vals
    g = str(x or "").strip().lower()
    return (g.split(" ")[0] if g else "", (), ())

def menu_actions():
    acts = set()
    p = os.path.join(BASE, "runeval.py")
    try:
        src = open(p).read()
        for line in src.splitlines():
            line = line.strip()
            if line.startswith("'") or line.startswith('"'):
                line = line.strip("'\"")
                if " " in line and line.split(" ")[0].isidentifier() and "{" in line:
                    acts.add(line.split(" ")[0])
    except Exception:
        pass
    return acts or {"read_url", "save_claim", "write_note", "remember", "queue_task", "execute_code", "none"}

def main():
    hp = os.path.join(BASE, "eval_history.jsonl")
    if not os.path.exists(hp):
        print("DIAG: no eval_history.jsonl yet, run runeval.py first")
        return 1
    runs = []
    with open(hp) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                runs.append(json.loads(line))
            except Exception:
                pass
    if not runs:
        print("DIAG: eval_history is empty")
        return 1
    last = runs[-1]
    fails = [r for r in last.get("results", []) if not r.get("ok")]
    if not fails:
        print("DIAG: latest run " + str(last.get("pass")) + "/" + str(last.get("total")) + " passed, nothing to triage")
        return 0
    acts = menu_actions()
    print("DIAG latest run " + str(last.get("when", "?")) + " mode " + str(last.get("mode", "?")) + " " + str(last.get("pass")) + "/" + str(last.get("total")))
    for r in fails:
        tid = r.get("id")
        frozen = None
        for run in reversed(runs[:-1]):
            hit = None
            for rr in run.get("results", []):
                if rr.get("id") == tid and rr.get("ok"):
                    hit = rr
                    break
            if hit is not None:
                frozen = hit
                break
        new = norm(r.get("act") if r.get("act") else r.get("got"))
        if frozen is None:
            print(tid + " -> FIRST_OBSERVATION: no passing run on record yet, nothing to diff against")
            continue
        old = norm(frozen.get("act") if frozen.get("act") else frozen.get("got"))
        if old[0] and old[0] not in acts:
            print(tid + " -> TASK_STALE: last pass used action " + old[0] + " which is no longer on her menu")
        elif new == old:
            print(tid + " -> MODEL_REGRESSION: identical action shape as last pass (" + old[0] + ") but worse outcome")
        elif old[0] == new[0]:
            print(tid + " -> BEHAVIOR_CHANGED: same action " + old[0] + " but different arguments than last pass, give it a human look")
        else:
            print(tid + " -> BEHAVIOR_CHANGED: was " + old[0] + " at last pass, now " + new[0] + ", give it a human look")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
