#!/usr/bin/env python3
# patch_actonly.py - pins griselda to act-only: appends an act-first, no-story
# rule to rules.txt so messages from Kyle get real tool actions, not roleplay.
# Backs up rules.txt first. rules.txt stays hers to self-edit as before.
import os, shutil, sys

BASE = os.path.expanduser("~/griselda-brain")
P = os.path.join(BASE, "rules.txt")
NL = chr(10)
LINE = "act first: when kyle sends you a message, choose a real action from your toolset that does what he asked and do it. no story prose, no narration, no roleplay filler in replies; answer with actions and short status lines only."

def main():
    if not os.path.exists(P):
        print("ABORT: rules.txt not found at " + P)
        return 1
    src = open(P).read()
    if "act first: when kyle sends you a message" in src:
        print("already patched, nothing to do")
        return 0
    shutil.copy2(P, P + ".bakact")
    out = src.rstrip(NL) + NL + NL + LINE + NL
    open(P, "w").write(out)
    print("rules.txt updated: act-first rule appended")
    tail = out.split(NL)
    for l in tail[-4:]:
        if l.strip():
            print("  " + l)
    print("backup: rules.txt.bakact")
    return 0

sys.exit(main())
