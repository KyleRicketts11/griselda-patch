#!/usr/bin/env python3
# wire_editrules2.py - step 2 retry: handler pinned to the action-list line itself
# money stays locked, everything else she can change herself
import shutil, py_compile

TARGET = "agent.py"
BACKUP = TARGET + ".bakrules3"
NL = chr(10)

TUPLE_OLD = '("read_url", "save_claim", "write_note", "remember", "queue_task", "execute_code"):'
TUPLE_NEW = '("read_url", "save_claim", "write_note", "remember", "queue_task", "execute_code", "edit_rules"):'

HANDLER = NL.join([
    '            if act.get("action") == "edit_rules":',
    '                _r = str(act.get("rule", "")).strip()[:300]',
    '                _low = _r.lower()',
    '                if not _r:',
    '                    _res = "[rules] empty rule edit, skipped."',
    '                elif "money" in _low:',
    '                    _res = "[rules] the money rule is Kyles, she may not change it."',
    '                else:',
    '                    try:',
    '                        with open(RULES_PATH, "a", encoding="utf-8") as _rf:',
    '                            _rf.write(time.strftime("%Y-%m-%d %H:%M", time.gmtime()) + " griselda added: " + _r + chr(10))',
    '                        _res = "[rules] rule added: " + _r',
    '                    except Exception as _exc:',
    '                        _res = "[rules] rules write failed: " + str(_exc)',
    '                print(_res)',
    '                contents.append({"role": "user", "parts": [{"text": "tool result: " + _res}]})',
    '                continue',
])


def main():
    src = open(TARGET, encoding="utf-8").read()
    if "edit_rules" in src:
        print("ALREADY PATCHED or edit_rules already exists, nothing to do")
        return 0
    n = src.count(TUPLE_OLD)
    if n == 0:
        print("ABORT: action-list line not found, nothing changed")
        raise SystemExit(1)
    if n > 1:
        print("ABORT: action-list line found " + str(n) + " times, nothing changed")
        raise SystemExit(1)
    shutil.copy2(TARGET, BACKUP)
    print("backup: " + BACKUP)
    src = src.replace(TUPLE_OLD, TUPLE_NEW + NL + HANDLER, 1)
    print("edit_rules added to her action list + handler wired (money refused, rest hers)")
    open(TARGET, "w", encoding="utf-8").write(src)
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
