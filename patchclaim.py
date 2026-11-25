#!/usr/bin/env python3
# patchclaim.py - claim ledger v1 for griselda-brain
# Upgrades save_claim into a real ledger (claim ids, duplicate blocking, status field)
# and adds a lookup_claim action she can use before stating a fact.
# Safety: refuses if already applied or backup exists, anchors must match exactly once,
# backs up to agent.py.bakclaim, py_compile check with restore-on-fail.
# Undo: python patchclaim.py undo
import os, sys, shutil, re, py_compile

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "griselda-brain")
AGENT = os.path.join(BASE, "agent.py")
BAK = os.path.join(BASE, "agent.py.bakclaim")

NEW_SAVE = chr(10).join([
"def _save_claim(args):",
"    import json as _cj",
"    import time as _ct",
"    path = os.path.join(BASE_DIR, 'claims.json')",
"    claims = []",
"    if os.path.exists(path):",
"        try:",
"            with open(path, 'r', encoding='utf-8') as f:",
"                claims = _cj.load(f)",
"            if not isinstance(claims, list):",
"                claims = []",
"        except Exception:",
"            claims = []",
"    text = str(args.get('claim', '')).strip()[:500]",
"    key = ' '.join(text.lower().split())",
"    if key:",
"        for old in claims:",
"            otext = str(old.get('claim', '')).strip()[:500]",
"            okey = ' '.join(otext.lower().split())",
"            if key == okey:",
"                return 'claim already in ledger (id ' + str(old.get('id', '?')) + ', saved ' + str(old.get('at', '?')) + ')'",
"    entry = {",
"        'id': 'cl-' + _ct.strftime('%Y%m%d%H%M%S', _ct.gmtime()),",
"        'claim': text,",
"        'source': str(args.get('source', args.get('target', '')))[:200],",
"        'revealed': str(args.get('revealed', 'unknown'))[:80],",
"        'status': 'unverified',",
"        'at': _ct.strftime('%Y-%m-%d %H:%M', _ct.gmtime()),",
"    }",
"    claims.append(entry)",
"    try:",
"        with open(path, 'w', encoding='utf-8') as f:",
"            _cj.dump(claims, f, ensure_ascii=False, indent=1)",
"        return 'claim saved as ' + entry['id'] + ' (' + str(len(claims)) + ' total now)'",
"    except Exception as e:",
"        return 'claim save failed: ' + str(e)",
"",
"",
"def _lookup_claim(args):",
"    import json as _cj",
"    path = os.path.join(BASE_DIR, 'claims.json')",
"    claims = []",
"    if os.path.exists(path):",
"        try:",
"            with open(path, 'r', encoding='utf-8') as f:",
"                claims = _cj.load(f)",
"            if not isinstance(claims, list):",
"                claims = []",
"        except Exception:",
"            claims = []",
"    if not claims:",
"        return 'claim ledger is empty'",
"    query = str(args.get('query', '')).strip().lower()",
"    words = [w for w in query.split() if len(w) >= 4]",
"    if not words:",
"        picks = claims[-5:]",
"    else:",
"        scored = []",
"        for c in claims:",
"            ctext = str(c.get('claim', '')).lower()",
"            hit = sum(1 for w in words if w in ctext)",
"            if hit > 0:",
"                scored.append((hit, c))",
"        scored.sort(key=lambda t: t[0], reverse=True)",
"        picks = [c for _h, c in scored[:3]]",
"        if not picks:",
"            return 'no claims in your ledger match: ' + query",
"    lines = []",
"    for c in picks:",
"        lines.append(str(c.get('id', '?')) + ' [' + str(c.get('status', 'unverified')) + '] ' + str(c.get('claim', ''))[:160] + ' (source: ' + str(c.get('source', 'unknown'))[:60] + ', saved ' + str(c.get('at', '?')) + ')')",
"    return 'claim ledger hits:' + chr(10) + chr(10).join(lines)",
"",
"",
])

MENU_LINE = "    " + chr(39) + '{"action": "lookup_claim", "query": "..."} searches your own claim ledger before you state a fact. ' + chr(39)

def fail(msg):
    print("PATCH-FAIL: " + msg)
    sys.exit(1)

src = open(AGENT, "r", encoding="utf-8").read()

if "def _lookup_claim" in src:
    fail("already applied (found def _lookup_claim), nothing to do")
if os.path.exists(BAK):
    fail("backup already exists, refusing to run twice")
if "def _save_claim" not in src:
    fail("could not find def _save_claim in agent.py")

lines = src.split(chr(10))

# 1. replace the whole _save_claim block with the ledger version + _lookup_claim
starts = [i for i, l in enumerate(lines) if l.startswith("def _save_claim")]
if len(starts) != 1:
    fail("expected exactly one 'def _save_claim' line, found " + str(len(starts)))
s = starts[0]
e = None
for j in range(s + 1, len(lines)):
    l = lines[j]
    if l.strip() == "":
        continue
    if not l[0].isspace():
        e = j
        break
if e is None:
    fail("could not find the end of _save_claim (no next top-level line)")
while e > s and lines[e - 1].strip() == "":
    e -= 1
new_lines = lines[:s] + NEW_SAVE.rstrip(chr(10)).split(chr(10)) + ["", ""] + lines[e:]

# 2. run_tool dispatch: mirror the save_claim branch for lookup_claim
disp = []
for i, l in enumerate(new_lines):
    if "lookup" in l or "def _save_claim" in l or "_save_claim(args" in l:
        continue
    if "in (" in l:
        continue
    if ("save_claim" in l) and ("return" in l or "==" in l):
        disp.append(i)
if len(disp) != 1:
    fail("expected exactly one save_claim dispatch line in run_tool, found " + str(len(disp)))
di = disp[0]
dline = new_lines[di]
indent = dline[:len(dline) - len(dline.lstrip())]
if "return" in dline:
    ins = [indent + 'elif name == "lookup_claim": return _lookup_claim(arguments)']
else:
    nxt = new_lines[di + 1] if di + 1 < len(new_lines) else ""
    nindent = nxt[:len(nxt) - len(nxt.lstrip())] if nxt.strip() else indent + "    "
    ins = [indent + 'elif name == "lookup_claim":', nindent + "return _lookup_claim(arguments)"]
new_lines = new_lines[:di + 1] + ins + new_lines[di + 1:]

# 3. text-JSON whitelist: add lookup_claim to the tuple that already lists save_claim
wl = [i for i, l in enumerate(new_lines) if "in (" in l and "save_claim" in l and "lookup" not in l]
if len(wl) != 1:
    fail("expected exactly one text-JSON whitelist line listing save_claim, found " + str(len(wl)))
wi = wl[0]
wline = new_lines[wi]
m = re.search(r'save_claim(\s*\))', wline)
if m:
    wline2 = wline[:m.start()] + 'save_claim", "lookup_claim' + wline[m.end() - 1:]
else:
    wline2 = wline.replace('"save_claim"', '"save_claim", "lookup_claim"', 1)
new_lines[wi] = wline2

# 4. teach her menu: insert a lookup_claim line after the queue_task menu line
menu = [i for i, l in enumerate(new_lines) if "queue_task" in l and "queues a task" in l]
if len(menu) != 1:
    fail("expected exactly one queue_task menu line, found " + str(len(menu)))
mi = menu[0]
mline = new_lines[mi]
mind = mline[:len(mline) - len(mline.lstrip())]
new_lines.insert(mi + 1, mind + MENU_LINE.lstrip())

out = chr(10).join(new_lines)

shutil.copy2(AGENT, BAK)
open(AGENT, "w", encoding="utf-8").write(out)
try:
    py_compile.compile(AGENT, doraise=True)
except Exception as ex:
    shutil.copy2(BAK, AGENT)
    fail("compile check failed, agent.py restored from backup: " + str(ex))

print("PATCH-OK: claim ledger v1 live")
print("backup: agent.py.bakclaim")
print("new: save_claim blocks duplicates and saves id + status; lookup_claim searches the ledger")
print("undo: python patchclaim.py undo")

if len(sys.argv) > 1 and sys.argv[1] == "undo":
    shutil.copy2(BAK, AGENT)
    print("UNDONE: agent.py restored from agent.py.bakclaim")
