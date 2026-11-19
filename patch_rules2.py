#!/usr/bin/env python3
# patch_rules2.py - step 1 of self-editing rules: persona line + rules.txt reset
# safe: backups first, aborts clean, and dumps the action-handler region for step 2
import os, shutil, py_compile

TARGET = "agent.py"
BACKUP = TARGET + ".bakrules2"
NL = chr(10)


def die(msg):
    print("ABORT: " + msg)
    raise SystemExit(1)


def main():
    if not os.path.exists(TARGET):
        die("agent.py not found (run from ~/griselda-brain)")
    src = open(TARGET, encoding="utf-8").read()
    lines = src.split(NL)

    old_persona = "never touch accounts, logins, or money"
    n = src.count(old_persona)
    if n == 0:
        die("persona line not found")
    if n > 1:
        die("persona line found " + str(n) + " times, need exactly 1")

    print("--- dump start (for step 2 wiring) ---")
    for a, b in ((88, 102), (320, 345), (575, 680)):
        for i in range(a, min(b, len(lines)) + 1):
            print(str(i) + ": " + lines[i - 1][:170])
    print("--- dump end ---")

    shutil.copy2(TARGET, BACKUP)
    print("backup: " + BACKUP)

    src = src.replace(old_persona, "never touch money without asking Kyle first", 1)
    print("persona: accounts/logins restriction removed, money lock kept")

    RULES = "rules.txt"
    old_rules = ""
    if os.path.exists(RULES):
        old_rules = open(RULES, encoding="utf-8").read()
        shutil.copy2(RULES, RULES + ".bak")
    open("rules_old_dump.txt", "w", encoding="utf-8").write(old_rules)
    print("old rules saved to rules_old_dump.txt (" + str(len(old_rules.splitlines())) + " lines)")
    new_rules = NL.join([
        "Rules for Griselda (read every cycle):",
        "- LOCKED: never touch real-world money. If a task would cost money, stop and ask Kyle first. (only Kyle can change this line)",
        "- you may log in to sites and fill in forms when a task needs it",
        "- you may change any other rule in this file yourself with the edit_rules action (wired next)",
    ]) + NL
    open(RULES, "w", encoding="utf-8").write(new_rules)
    print("rules.txt reset: money locked, rest is hers to change")

    open(TARGET, "w", encoding="utf-8").write(src)
    try:
        py_compile.compile(TARGET, doraise=True)
    except Exception as e:
        shutil.copy2(BACKUP, TARGET)
        die("compile failed, backup restored: " + str(e)[:300])
    print("COMPILE-OK")
    print("next: step 2 wires edit_rules into her action handler")
    return 0


raise SystemExit(main())
