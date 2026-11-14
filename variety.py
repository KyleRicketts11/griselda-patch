#!/usr/bin/env python3
# variety.py - griselda variety nudge: teaches her autonomy prompt to stop
# re-picking the same subject (the tea loop). Backs up agent.py first.
# undo: python variety.py undo
import os, sys, shutil, py_compile

NL = chr(10)
HOME = os.path.expanduser("~")
if len(sys.argv) > 1 and sys.argv[1] == "undo":
    d = sys.argv[2] if len(sys.argv) > 2 else HOME + "/griselda-brain"
    b = os.path.join(d, "agent.py.bakvariety")
    if os.path.exists(b):
        shutil.copy(b, os.path.join(d, "agent.py"))
        print("restored agent.py from backup")
    else:
        print("no backup found:", b)
    sys.exit(0)

D = sys.argv[1] if len(sys.argv) > 1 else HOME + "/griselda-brain"
P = os.path.join(D, "agent.py")
src = open(P, encoding="utf-8").read()
if "VARIETY RULE" in src:
    print("already patched, nothing to do"); sys.exit(0)

A1S = 'seed = " | ".join(seeds) or "nothing yet"'
A2S = '"Memory for inspiration: " + seed'
lines = src.splitlines()
out = []
done1 = done2 = False
for ln in lines:
    s = ln.strip()
    ind = ln[:len(ln) - len(ln.lstrip())]
    if not done1 and s == A1S:
        out.append(ln)
        out.append(ind + "recents = []")
        out.append(ind + "for t in tasks[-8:]:")
        out.append(ind + '    rt = str(t.get("target", "") or t.get("url", "") or t.get("task", ""))')
        out.append(ind + "    if rt:")
        out.append(ind + "        recents.append(rt[:90])")
        out.append(ind + 'recent = " | ".join(recents) or "none yet"')
        done1 = True
        continue
    if not done2 and s == A2S:
        out.append(ind + '"Memory for inspiration: " + seed + " VARIETY RULE: your recent picks were: " + recent + ". Do not pick any of those or anything in the same subject area. Pick a task on a topic you have never touched. If you cannot think of one, rest."')
        done2 = True
        continue
    out.append(ln)
if not (done1 and done2):
    print("ABORT: anchor missing, nothing written", done1, done2); sys.exit(1)
bak = os.path.join(D, "agent.py.bakvariety")
shutil.copy(P, bak)
open(P, "w", encoding="utf-8").write(NL.join(out) + NL)
try:
    py_compile.compile(P, doraise=True)
    print("backup:", bak)
    print("WROTE agent.py")
    print("variety nudge is live in her autonomy prompt. restart her with run_unified.py to load it.")
    print("undo: python variety.py undo")
except Exception as e:
    shutil.copy(bak, P)
    print("compile failed, restored backup:", e)
    sys.exit(1)
