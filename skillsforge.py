#!/usr/bin/env python3
# skillsforge.py - griselda's skill forge (the Brahma steal)
# creates skills.py (save/run/list named code snippets in skills.json)
# and adds ONE menu line to agent.py teaching her to use it.
# no dispatch or whitelist changes: it all rides her existing execute_code.
# safe: backs up agent.py to agent.py.bakforge, compile-checks, restores on
# any failure. undo: python skillsforge.py undo
import os, shutil, sys, ast
NL = chr(10)
P = "agent.py"
BAK = P + ".bakforge"

SKILLS_PY = '''# skills.py - griselda's skill forge: save working snippets, run them by name
import json, os, time
PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills.json")

def _load():
    if os.path.exists(PATH):
        with open(PATH) as f:
            return json.load(f)
    return {}

def save(name, code, note=""):
    s = _load()
    s[name] = {"code": code, "note": note, "saved": time.strftime("%Y-%m-%d %H:%M:%S")}
    with open(PATH, "w") as f:
        json.dump(s, f, indent=1)
    return "saved skill " + name + " (" + str(len(s)) + " total)"

def run(name, **ctx):
    s = _load()
    if name not in s:
        return "no skill named " + name
    g = dict(ctx)
    exec(s[name]["code"], g)
    return "ran skill " + name

def list():
    return {k: v.get("note", "") for k, v in _load().items()}
'''

MENU_LINE = '{"action": "execute_code", "code": "import skills; skills.save(\'name\', code)"} forge: save working code as a named skill; skills.run(\'name\') runs it again, skills.list() shows saved ones. '

if len(sys.argv) > 1 and sys.argv[1].lower() == "undo":
    shutil.copy(BAK, P)
    print("UNDO_OK restored " + BAK + " over " + P)
    sys.exit(0)

try:
    src = open(P).read()
except FileNotFoundError:
    print("ABORT: agent.py not found, run from ~/griselda-brain")
    sys.exit(1)

try:
    ast.parse(src)
except SyntaxError as e:
    print("ABORT: agent.py does not compile before patch: " + str(e))
    sys.exit(1)

if "skills.save" in src:
    print("ALREADY_PATCHED: forge menu line already in agent.py")
else:
    shutil.copy(P, BAK)
    print("backup: " + BAK)
    lines = src.split(NL)
    mi = -1
    for i, line in enumerate(lines):
        if ('{"action": "execute_code"' in line) and ("sandbox" in line):
            mi = i
            break
    if mi == -1:
        for i, line in enumerate(lines):
            if '{"action": "queue_task"' in line:
                mi = i
                break
    if mi == -1:
        print("MENU_NEEDED: no execute_code menu literal found. lines with action:")
        for i, line in enumerate(src.split(NL), 1):
            if '{"action": "' in line:
                print(str(i) + ": " + line.strip()[:110])
        print("PARTIAL: nothing written, backup kept")
        sys.exit(1)
    raw = lines[mi]
    ind = raw[:len(raw) - len(raw.lstrip())]
    body = raw.lstrip()
    q = "'" if body.startswith("'") else '"'
    comma = "," if raw.rstrip().endswith(q + ",") else ""
    body_text = MENU_LINE.replace(q, q + q)
    ins = ind + q + body_text + q + comma
    lines[mi + 1:mi + 1] = [ins]
    out = NL.join(lines)
    try:
        ast.parse(out)
    except SyntaxError as e:
        shutil.copy(BAK, P)
        print("ABORT: patched file failed compile, restored backup. " + str(e))
        sys.exit(1)
    open(P, "w").write(out)
    print("MENU_OK forge line after line " + str(mi + 1))
    print("WROTE " + P)

# skills.py: create only if missing or markerless (never clobber a real one)
if not os.path.exists("skills.py"):
    open("skills.py", "w").write(SKILLS_PY)
    print("WROTE skills.py (fresh)")
elif "skill forge" not in open("skills.py").read():
    shutil.copy("skills.py", "skills.py.userbak")
    open("skills.py", "w").write(SKILLS_PY)
    print("WROTE skills.py (old one kept as skills.py.userbak)")
else:
    print("SKILLS_OK skills.py already in place")
ast.parse(open("skills.py").read())
print("DONE. restart her with run_unified.py so the forge line loads. undo: python skillsforge.py undo")
