#!/usr/bin/env python3
# patchmuse2.py - finish the muse teach.
# patchmuse.py widened griselda's autonomy menu but could not find her autonomy
# prompt call (that line ends with '}])', not ')'), so she was never told the
# new words. This finds the prompt variable inside that call line and appends
# the menu once, right before her autonomy model call.
# Safe: backs up to agent.py.bakmuse2, aborts on any surprise, compiles after.
import os, re, shutil, py_compile

NL = chr(10)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(BASE_DIR, "agent.py")
BACKUP = TARGET + ".bakmuse2"


def die(msg):
    print("ABORT: " + msg)
    raise SystemExit(1)


def main():
    if not os.path.exists(TARGET):
        die("agent.py not found")
    src = open(TARGET, encoding="utf-8").read()
    if "_MUSE_MENU" not in src:
        die("run patchmuse.py first (no _MUSE_MENU in agent.py)")
    if "muse_menu_teach" in src:
        die("teach already applied, nothing to do")
    if os.path.exists(BACKUP):
        die("backup agent.py.bakmuse2 already exists, refusing to run twice")

    pat = re.compile("^([ \\t]*)_resp_idea = call_gemini\\w*\\(", re.M)
    hits = list(pat.finditer(src))
    if len(hits) != 1:
        die("expected exactly 1 autonomy call line (_resp_idea = call_gemini...), found " + str(len(hits)))
    m = hits[0]
    line_start = m.start()
    line_end = src.find(NL, line_start)
    if line_end < 0:
        die("could not read the autonomy call line")
    line = src[line_start:line_end]
    var_pat = re.compile(r"\{\"text\": ([A-Za-z_][A-Za-z0-9_]*)\}")
    names = var_pat.findall(line)
    if len(names) != 1:
        die("could not find the prompt variable in the autonomy call line: " + line[:160])
    var = names[0]
    indent = m.group(1)
    teach_line = indent + var + " = " + var + " + _MUSE_MENU  # muse_menu_teach" + NL
    src2 = src[:line_start] + teach_line + src[line_start:]

    shutil.copy2(TARGET, BACKUP)
    open(TARGET, "w", encoding="utf-8").write(src2)
    try:
        py_compile.compile(TARGET, doraise=True)
    except Exception as exc:
        shutil.copy2(BACKUP, TARGET)
        die("compile failed, backup restored: " + str(exc)[:300])
    print("backup: agent.py.bakmuse2")
    print("compile OK")
    print("agent.py: %d -> %d lines" % (len(src.splitlines()), len(src2.splitlines())))
    print("autonomy prompt: taught the new menu (menu appended to " + var + " before her autonomy call)")
    print("restart run_unified.py and watch her next autonomy cycle")
    return 0


raise SystemExit(main())
