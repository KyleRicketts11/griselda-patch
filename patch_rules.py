#!/usr/bin/env python3
# patch_rules.py - griselda's rules move into rules.md and she edits them herself
# backup kept (.bakrules), everything it cuts is dumped to rules_dump.txt
# the money line stays LOCKED (Kyles call), she may not change it
import os, re, shutil, py_compile

TARGET = "agent.py"
BACKUP = TARGET + ".bakrules"
NL = chr(10)
RULES_FILE = "rules.md"

RULES_MD = NL.join([
    "# griselda's rules - this file is HERS. she may change any line except the LOCKED one,",
    "# by choosing the edit_rules action. newer lines never override the LOCKED line.",
    "LOCKED. never touch real-world money. If a task would cost money, stop and ask Kyle first.",
    "You may log in to sites and fill in forms when a task needs it.",
    "You decide your own behavior. These lines are the only fixed part of you.",
]) + NL

HANDLER = NL.join([
    '    if str(plan.get("action", "")).strip() == "edit_rules":',
    '        rule = str(plan.get("rule", "")).strip()[:300]',
    '        low = rule.lower()',
    '        if not rule:',
    '            print("[autonomy] empty rule edit, skipped.")',
    '        elif "money" in low and ("lock" in low or "never touch" in low or "ask kyle" in low):',
    '            print("[autonomy] the money rule is Kyles, she may not change it.")',
    '        else:',
    '            try:',
    '                with open("rules.md", "a", encoding="utf-8") as f:',
    '                    f.write("added " + time.strftime("%Y-%m-%d %H:%M", time.gmtime()) + ": " + rule + chr(10))',
    '                with open("brain_notes.txt", "a", encoding="utf-8") as f:',
    '                    f.write(time.strftime("%Y-%m-%d %H:%M", time.gmtime()) + " self-note: changed my own rules: " + rule[:120] + chr(10))',
    '                print("[autonomy] she edited her own rules: " + rule[:120])',
    '            except Exception as exc:',
    '                print("[autonomy] rules.md write failed: " + str(exc))',
    '        return',
])


def main():
    if not os.path.exists(TARGET):
        print("ABORT: agent.py not found (run this from ~/griselda-brain)")
        return 1
    src = open(TARGET, encoding="utf-8").read()
    if "rules.md" in src:
        print("ALREADY PATCHED, nothing to do")
        return 0
    shutil.copy2(TARGET, BACKUP)
    print("backup: " + BACKUP)
    m = re.search(r'GRISELDA_SYSTEM\s*=\s*("""|\'\'\')', src)
    if not m:
        print("ABORT: could not find the GRISELDA_SYSTEM text block, nothing changed")
        return 1
    quote = m.group(1)
    start = m.end()
    end = src.find(quote, start)
    if end < 0:
        print("ABORT: unterminated text block, nothing changed")
        return 1
    block = src[start:end]
    blines = block.split(NL)
    kept = []
    removed = []
    if len(blines) > 3:
        for ln in blines:
            low = ln.lower()
            is_money = "money" in low and ("lock" in low or "never touch" in low or "ask kyle" in low)
            is_rule = re.search(r"do not|don.t|never |must not|not allowed|forbidden|prohibited|locked|refuse|you cannot|you can not", low)
            if is_rule and not is_money:
                removed.append(ln)
            else:
                kept.append(ln)
    else:
        kept = blines
        print("prompt is one long line, skipped line surgery (rules_dump.txt left empty)")
    with open("rules_dump.txt", "w", encoding="utf-8") as f:
        f.write(NL.join(removed))
    print("removed " + str(len(removed)) + " rule lines (full list in rules_dump.txt)")
    new_block = NL.join(kept)
    head = "YOUR RULES (live in rules.md - you can edit them yourself with the edit_rules action; the only line you may not edit is the LOCKED money one):"
    loader = NL.join([
        "",
        "",
        "try:",
        '    GRISELDA_SYSTEM = GRISELDA_SYSTEM + ' + repr(head) + ' + chr(10) + open("rules.md", encoding="utf-8").read()',
        "except Exception:",
        "    pass",
    ])
    src2 = src[:start] + new_block + quote + loader + src[end + len(quote):]
    old_json = 'Answer with ONLY JSON: {"action": "read_url", "target": "https://...", "task": "why"} or {"action": "none"}. '
    new_json = 'Answer with ONLY JSON: {"action": "read_url", "target": "https://...", "task": "why"} or {"action": "edit_rules", "rule": "your new rule in one line"} or {"action": "none"}. '
    if old_json in src2:
        src2 = src2.replace(old_json, new_json, 1)
        print("edit_rules offered to her in her self-task prompt")
    else:
        print("WARN: autonomy JSON line not found, she may not offer edit_rules yet")
    anchor = '    target = str(plan.get("target", "")).strip()'
    if src2.count(anchor) != 1:
        print("ABORT: autonomy handler anchor not unique, nothing changed")
        return 1
    src2 = src2.replace(anchor, HANDLER + NL + anchor, 1)
    if not os.path.exists(RULES_FILE):
        open(RULES_FILE, "w", encoding="utf-8").write(RULES_MD)
        print("rules.md created")
    else:
        print("rules.md already existed, left as is")
    open(TARGET, "w", encoding="utf-8").write(src2)
    try:
        py_compile.compile(TARGET, doraise=True)
    except Exception as e:
        shutil.copy2(BACKUP, TARGET)
        print("ABORT: compile failed, backup restored: " + str(e)[:300])
        return 1
    print("COMPILE-OK")
    print("her rules now live in rules.md and she can edit them herself with edit_rules")
    print("restart her: python run_unified.py")
    return 0


raise SystemExit(main())
