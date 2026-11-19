#!/usr/bin/env python3
# wire_editrules3.py - adaptive-indent wiring of edit_rules into her action handler
# copies the real indentation from the file, so tabs or deeper nesting both work
import shutil, py_compile

TARGET = "agent.py"
BACKUP = TARGET + ".bakrules4"
NL = chr(10)
TAB = chr(9)

TUP = '("read_url", "save_claim", "write_note", "remember", "queue_task", "execute_code")'
TUP_NEW = '("read_url", "save_claim", "write_note", "remember", "queue_task", "execute_code", "edit_rules")'


def main():
    src = open(TARGET, encoding="utf-8").read()
    if "edit_rules" in src:
        print("ALREADY PATCHED, nothing to do")
        return 0
    lines = src.split(NL)
    hits = [i for i, ln in enumerate(lines) if (TUP + ":") in ln]
    if len(hits) != 1:
        print("ABORT: action-list line found " + str(len(hits)) + " times, nothing changed")
        raise SystemExit(1)
    idx = hits[0]
    print("found action list at line " + str(idx + 1))
    print("context before:")
    for k in range(max(0, idx - 1), min(idx + 4, len(lines))):
        print(str(k + 1) + ": " + repr(lines[k]))
    base = None
    for j in range(idx + 1, min(idx + 6, len(lines))):
        if lines[j].strip():
            base = lines[j][:len(lines[j]) - len(lines[j].lstrip())]
            break
    if not base:
        print("ABORT: could not read body indent, nothing changed")
        raise SystemExit(1)
    unit = TAB if TAB in base else "    "

    def ind(depth):
        return base + unit * depth

    H = [
        ind(0) + 'if act.get("action") == "edit_rules":',
        ind(1) + '_r = str(act.get("rule", "")).strip()[:300]',
        ind(1) + '_low = _r.lower()',
        ind(1) + 'if not _r:',
        ind(2) + '_res = "[rules] empty rule edit, skipped."',
        ind(1) + 'elif "money" in _low:',
        ind(2) + '_res = "[rules] the money rule is Kyles, she may not change it."',
        ind(1) + 'else:',
        ind(2) + 'try:',
        ind(3) + 'with open(RULES_PATH, "a", encoding="utf-8") as _rf:',
        ind(4) + '_rf.write(time.strftime("%Y-%m-%d %H:%M", time.gmtime()) + " griselda added: " + _r + chr(10))',
        ind(3) + '_res = "[rules] rule added: " + _r',
        ind(2) + 'except Exception as _exc:',
        ind(3) + '_res = "[rules] rules write failed: " + str(_exc)',
        ind(1) + 'print(_res)',
        ind(1) + 'contents.append({"role": "user", "parts": [{"text": "tool result: " + _res}]})',
        ind(1) + 'continue',
    ]
    shutil.copy2(TARGET, BACKUP)
    print("backup: " + BACKUP)
    lines[idx] = lines[idx].replace(TUP, TUP_NEW, 1)
    lines[idx + 1:idx + 1] = H
    open(TARGET, "w", encoding="utf-8").write(NL.join(lines))
    print("inserted handler after the action-list line")
    try:
        py_compile.compile(TARGET, doraise=True)
    except Exception as e:
        shutil.copy2(BACKUP, TARGET)
        print("ABORT: compile failed, backup restored: " + str(e)[:300])
        raise SystemExit(1)
    print("COMPILE-OK")
    print("restart her: python run_unified.py")
    return 0


raise SystemExit(main())
