#!/usr/bin/env python3
# purge.py - dedupe griselda's tasks.json: for each target keep the first
# queued task, drop the repeats. backup first, auto-restore on any failure.
# undo: python purge.py undo
import json, os, shutil, sys
NL = chr(10)
HOME = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/griselda-brain")
TP = os.path.join(HOME, "tasks.json")
BP = os.path.join(HOME, "tasks.json.bakpurge")

if len(sys.argv) > 1 and sys.argv[1] == "undo":
    if os.path.exists(BP):
        shutil.copy2(BP, TP)
        print("restored tasks.json from backup")
    else:
        print("no backup found, nothing to undo")
    raise SystemExit(0)

try:
    with open(TP) as f:
        data = json.load(f)
except Exception as e:
    print("ABORT: could not read tasks.json (" + str(e) + "), untouched")
    raise SystemExit(1)

if not isinstance(data, list) or not all(isinstance(t, dict) for t in data):
    print("ABORT: tasks.json is not a plain list of tasks (schema " + type(data).__name__ + "), untouched")
    raise SystemExit(1)

def tgt(t):
    return str(t.get("target") or t.get("url") or "").strip()

seen = set()
kept, dropped = [], 0
for t in data:
    u = tgt(t)
    if u and u in seen:
        dropped += 1
        continue
    if u:
        seen.add(u)
    kept.append(t)

if dropped == 0:
    print("already clean, no duplicates, wrote nothing")
    raise SystemExit(0)

shutil.copy2(TP, BP)
print("backup: tasks.json.bakpurge")

out = json.dumps(kept, indent=2, ensure_ascii=False)
with open(TP + ".tmp", "w") as f:
    f.write(out)
try:
    json.load(open(TP + ".tmp"))
except Exception as e:
    shutil.copy2(BP, TP)
    print("ABORT: rewritten file failed json check, restored backup. untouched")
    raise SystemExit(1)
os.replace(TP + ".tmp", TP)
print("kept " + str(len(kept)) + ", dropped " + str(dropped) + " duplicate tasks (same target, first kept)")
print("undo: python purge.py undo")
