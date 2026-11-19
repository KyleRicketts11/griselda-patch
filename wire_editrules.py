#!/usr/bin/env python3
# wire_editrules.py - step 2: wire edit_rules into griselda's action handler
# money stays locked, everything else she can change herself
import shutil, py_compile

TARGET = "agent.py"
BACKUP = TARGET + ".bakrules3"
NL = chr(10)

TUPLE_OLD = '("read_url", "save_claim", "write_note", "remember", "queue_task", "execute_code")'
TUPLE_NEW = '("read_url", "save_claim", "write_note", "remember", "queue_task", "execute_code", "edit_rules")'
NAME_OLD = 'name = act.get("action")'

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
    src = open(TARGET, encoding="utf-8").read()
    if "edit_rules" in src:
        print("ALREADY PATCHED or edit_rules already exists, nothing to do")
        return 0
    shutil.copy2(TARGET, BACKUP)
    print("backup: " + BACKUP)
    src = sub_once(src, TUPLE_OLD, TUPLE_NEW, "action tuple")
    print("edit_rules added to her action list")
    src = sub_once(src, NAME_OLD, NAME_OLD + NL + HANDLER, "handler insert")
    print("edit_rules handler wired (money refused, everything else she can add)")
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
