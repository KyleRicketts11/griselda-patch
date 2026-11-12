#!/usr/bin/env python3
# patchauto.py - stop griselda's autonomy loop from wasting Gemini calls.
# The loop passes the WHOLE raw API response (as a string) to the idea parser,
# so every good idea fails to parse and each cycle retries ~4 times.
# Fix: give the parser the model's actual text (the action idea itself),
# so a good idea parses on the first try: 1 call per cycle instead of ~4.
import os, re, shutil, py_compile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(BASE_DIR, "agent.py")
BACKUP = TARGET + ".bakauto"
NL = chr(10)


def main():
    if not os.path.exists(TARGET):
        print("ABORT: agent.py not found")
        return 1
    src = open(TARGET, "r").read()
    pat = re.compile(r"^([ \t]*)raw = str\(call_gemini\((.*)\)\)[ \t]*$", re.M)
    hits = pat.findall(src)
    if len(hits) != 1:
        print("ABORT: expected exactly 1 raw = str(call_gemini(...)) line, found %d, nothing changed" % len(hits))
        return 1
    ind, call_args = hits[0]
    shutil.copy2(TARGET, BACKUP)
    print("backup: " + os.path.basename(BACKUP))
    new_block = NL.join([
        ind + '_resp_idea = call_gemini(' + call_args + ')',
        ind + 'try:',
        ind + '    _parts_idea = _resp_idea.get("candidates", [{}])[0].get("content", {}).get("parts", [])',
        ind + '    raw = "".join(str(p.get("text", "")) for p in _parts_idea)',
        ind + 'except Exception:',
        ind + '    raw = str(_resp_idea)',
    ])
    src2 = pat.sub(lambda m: new_block, src, count=1)
    open(TARGET, "w").write(src2)
    try:
        py_compile.compile(TARGET, doraise=True)
    except Exception as e:
        shutil.copy2(BACKUP, TARGET)
        print("ABORT: compile failed, backup restored: " + str(e)[:300])
        return 1
    print("compile OK")
    print("agent.py: %d -> %d lines" % (len(src.splitlines()), len(src2.splitlines())))
    print("autonomy fix: her idea parser now sees the model's actual idea text")
    print("expected: 1 call per cycle instead of ~4, no more idea-not-readable spam")
    print("restart run_unified.py and watch one cycle to confirm")
    return 0


raise SystemExit(main())
