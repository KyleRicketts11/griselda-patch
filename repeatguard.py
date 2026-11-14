#!/usr/bin/env python3
# repeatguard.py - stops griselda re-queueing pages she already queued or read.
# inserts a guard right before her autonomy queue-append: if the picked target
# is already in tasks.json or her read-pages memory, she skips and rests
# instead. backup agent.py.bakguard, compile check, auto-restore on failure.
# undo: python repeatguard.py undo
import shutil, sys, os, py_compile
NL = chr(10)
_args = [x for x in sys.argv[1:] if x != "undo"]
HOME = _args[0] if _args else os.path.expanduser("~/griselda-brain")
AP = os.path.join(HOME, "agent.py")
BP = os.path.join(HOME, "agent.py.bakguard")
MARK = "REPEAT_GUARD_V1"

if "undo" in sys.argv[1:]:
    if os.path.exists(BP):
        shutil.copy2(BP, AP)
        print("restored agent.py from backup")
    else:
        print("no backup found, nothing to undo")
    raise SystemExit(0)

try:
    src = open(AP, encoding="utf-8").read()
except Exception as e:
    print("ABORT: could not read agent.py (" + str(e)[:80] + "), untouched")
    raise SystemExit(1)
if MARK in src:
    print("already installed, nothing to do")
    raise SystemExit(0)

lines = src.split(NL)
idx = None
for i, ln in enumerate(lines):
    if "tasks.append(" in ln and ("autonomy" in ln and "origin" in ln):
        idx = i
        break
if idx is None:
    print("ANCHOR NOT FOUND: no autonomy queue-append line. untouched.")
    for i, ln in enumerate(lines):
        if "origin" in ln and "autonomy" in ln:
            print(str(i + 1) + ": " + ln[:160])
    raise SystemExit(1)

indent = lines[idx][:len(lines[idx]) - len(lines[idx].lstrip())]
g = []
def a(s):
    g.append(indent + s)
a("# " + MARK + ": skip targets already queued or already read")
a("try:")
a("    _prior = load_tasks()")
a("    _seen = set()")
a("    for _t in _prior:")
a("        _u = str(_t.get(\"target\") or _t.get(\"url\") or \"\").strip()")
a("        if _u:")
a("            _seen.add(_u)")
a("    _pages = memory.get(\"pages\", [])")
a("    if isinstance(_pages, list):")
a("        for _p in _pages:")
a("            _u = str(_p.get(\"url\") if isinstance(_p, dict) else _p or \"\").strip()")
a("            if _u:")
a("                _seen.add(_u)")
a("    if target in _seen:")
a("        print(\"[autonomy] repeat guard: \" + target + \" already queued or read, skipping.\")")
a("        try:")
a("            with open(\"brain_notes.txt\", \"a\", encoding=\"utf-8\") as f:")
a("                f.write(time.strftime(\"%Y-%m-%d %H:%M\", time.gmtime()) + \" self-note: chose to skip a repeat and rest instead\" + chr(10))")
a("        except Exception:")
a("            pass")
a("        return")
a("except Exception:")
a("    pass")
lines[idx:idx] = g
out = NL.join(lines)
open(AP + ".tmp", "w", encoding="utf-8").write(out)
try:
    py_compile.compile(AP + ".tmp", doraise=True)
except Exception as e:
    try:
        os.remove(AP + ".tmp")
    except Exception:
        pass
    print("ABORT: patched file failed compile (" + str(e)[:120] + "), untouched")
    raise SystemExit(1)
shutil.copy2(AP, BP)
print("backup: agent.py.bakguard")
os.replace(AP + ".tmp", AP)
print("WROTE agent.py")
print("repeat guard is live before her autonomy queue line. restart her with run_unified.py to load it. undo: python repeatguard.py undo")
