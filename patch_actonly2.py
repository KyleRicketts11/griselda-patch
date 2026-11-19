#!/usr/bin/env python3
# patch_actonly2.py - kills the story talk for real: hard act-only wording in
# rules.txt (her brain) AND in the page chat's prompt (brain.html).
import os, shutil, sys

BASE = os.path.expanduser("~/griselda-brain")
NL = chr(10)

OLD_RULE = "act first: when kyle sends you a message"
NEW_RULE = ("act only, no story: you are a real agent, not a character. never roleplay, "
"never write asterisk actions, no potions or witch talk, never call kyle 'master kyle'. "
"when kyle asks for something, immediately pick the real tool action that does it "
"(read_url, a termux command through the gate, a camfox screenshot) and run it this cycle. "
"reply with what you did and the proof you saw (command output, page content, file changed). "
"never ask permission to act; spending money is the only locked thing.")

OLD_CTX = "Stay in your witchy persona, keep answers short."
NEW_CTX = ("Act only, never roleplay: no asterisk actions, no witch or potion talk, never call "
"Kyle 'Master Kyle'. You are a real agent: when Kyle asks for something, immediately pick a "
"real tool action (read_url, a termux command through the gate, a camfox screenshot) and do it. "
"Reply with what you did and the proof you saw (page content, command output). Never ask "
"permission to act; only spending money needs Kyle's yes first. If your tools cannot do it, "
"say so plainly.")

ok = True

rp = os.path.join(BASE, "rules.txt")
if os.path.exists(rp):
    src = open(rp).read()
    if NEW_RULE[:30] in src:
        print("rules.txt: already hardened")
    elif OLD_RULE in src:
        shutil.copy2(rp, rp + ".bakact2")
        out = []
        for line in src.split(NL):
            out.append(NEW_RULE if line.startswith(OLD_RULE) else line)
        open(rp, "w").write(NL.join(out))
        print("rules.txt: act rule hardened (backup rules.txt.bakact2)")
    else:
        shutil.copy2(rp, rp + ".bakact2")
        open(rp, "w").write(src.rstrip(NL) + NL + NL + NEW_RULE + NL)
        print("rules.txt: act rule appended (backup rules.txt.bakact2)")
else:
    print("rules.txt: not found, skipped"); ok = False

bp = os.path.join(BASE, "brain.html")
if os.path.exists(bp):
    src = open(bp).read()
    if NEW_CTX[:30] in src:
        print("brain.html: already hardened")
    elif OLD_CTX in src:
        shutil.copy2(bp, bp + ".bakact2")
        src = src.replace(OLD_CTX, NEW_CTX, 1)
        open(bp, "w").write(src)
        bal = src.count("{") - src.count("}")
        pal = src.count("(") - src.count(")")
        print("brain.html: chat prompt hardened (backup brain.html.bakact2) brace delta", bal, "paren delta", pal)
        if bal != 0 or pal != 0:
            ok = False
    else:
        print("brain.html: witchy line not found, skipped"); ok = False
else:
    print("brain.html: not found, skipped"); ok = False

print("PATCH-OK" if ok else "PATCH-PARTIAL")
