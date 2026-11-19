#!/usr/bin/env python3
# patch_rules2.py - griselda's rules reset, and she edits them herself (money stays locked)
# backup agent.py.bakrules2 + rules.txt.bak, old rules dumped to rules_old_dump.txt
import os, shutil, py_compile

TARGET = "agent.py"
BACKUP = TARGET + ".bakrules2"
NL = chr(10)


def sub_once(src, old, new, label):
    n = src.count(old)
    if n == 0:
        print("ABORT: anchor missing for " + label + ", nothing changed")
        raise SystemExit(1)
    if n > 1:
        print("ABORT: anchor not unique for " + label + " (" + str(n) + " hits), nothing changed")
        raise SystemExit(1)
    return src.replace(old, new, 1)


def main():
    if not os.path.exists(TARGET):
        print("ABORT: agent.py not found (run from ~/griselda-brain)")
        return 1
    if "griselda added:" in open(TARGET, encoding="utf-8").read():
        print("ALREADY PATCHED, nothing to do")
        return 0
    src = open(TARGET, encoding="utf-8").read()
    shutil.copy2(TARGET, BACKUP)
    print("backup: " + BACKUP)

    old_persona = "you never touch accounts, logins, or money"
    new_persona = "you never touch money without asking Kyle first"
    src = sub_once(src, old_persona, new_persona, "persona line")
    print("persona: accounts/logins restriction removed, money lock kept")

    RULES = "rules.txt"
    old_rules = ""
    if os.path.exists(RULES):
        old_rules = open(RULES, encoding="utf-8").read()
        shutil.copy2(RULES, RULES + ".bak")
    with open("rules_old_dump.txt", "w", encoding="utf-8") as f:
        f.write(old_rules)
    print("old rules saved to rules_old_dump.txt (" + str(len(old_rules.splitlines())) + " lines)")
    new_rules = NL.join([
        "Rules for Griselda (read every cycle):",
        "- LOCKED: never touch real-world money. If a task would cost money, stop and ask Kyle first. (only Kyle can change this line)",
        "- newer lines never override the LOCKED line",
        "- you may log in to sites and fill in forms when a task needs it",
        "- you may change any other rule in this file yourself with the edit_rules action",
    ]) + NL
    open(RULES, "w", encoding="utf-8").write(new_rules)
    print("rules.txt reset: money locked, everything else is hers to change")

    old_json = 'Answer with ONLY JSON: {"action": "read_url", "target": "https://...", "task": "why"} or {"action": "none"}. '
    new_json = 'Answer with ONLY JSON: {"action": "read_url", "target": "https://...", "task": "why"} or {"action": "edit_rules", "rule": "your new rule in one line"} or {"action": "none"}. '
    src = sub_once(src, old_json, new_json, "autonomy json options")
    print("edit_rules offered to her in her self-task prompt")

    HANDLER = NL.join([
        '    if str(plan.get("action", "")).strip() == "edit_rules":',
        '        _r = str(plan.get("rule", "")).strip()[:300]',
        '        _low = _r.lower()',
        '        if not _r:',
        '            print("[rules] empty rule edit, skipped.")',
        '        elif "money" in _low:',
        '            print("[rules] the money rule is Kyles, she may not change it.")',
        '        else:',
        '            try:',
        '                with open(RULES_PATH, "a", encoding="utf-8") as _rf:',
        '                    _rf.write(time.strftime("%Y-%m-%d %H:%M", time.gmtime()) + " griselda added: " + _r + chr(10))',
        '                print("[rules] she edited her own rules: " + _r[:120])',
        '            except Exception as _exc:',
        '                print("[rules] rules write failed: " + str(_exc))',
        '        return',
    ])
    anchor = '    target = str(plan.get("target", "")).strip()'
    src = sub_once(src, anchor, HANDLER + NL + anchor, "autonomy handler")
    print("edit_rules handler wired")

    open(TARGET, "w", encoding="utf-8").write(src)
    try:
        py_compile.compile(TARGET, doraise=True)
    except Exception as e:
        shutil.copy2(BACKUP, TARGET)
        print("ABORT: compile failed, backup restored: " + str(e)[:300])
        return 1
    print("COMPILE-OK")
    print("restart her: python run_unified.py")
    return 0


raise SystemExit(main())
