import shutil
shutil.copy("agent.py", "agent.py.bak10")
src = open("agent.py", encoding="utf-8").read()
nl = chr(10)
if "loop_mode = True" in src:
    print("already patched")
else:
    i = src.find("if loop_mode:")
    if i == -1:
        print("anchor not found")
        raise SystemExit(1)
    ls = src.rfind(nl, 0, i) + 1
    ind = src[ls:i]
    add = ind + 'if not [a for a in args if not a.startswith("--")]:' + nl + ind + "    loop_mode = True" + nl
    src = src[:ls] + add + src[ls:]
    open("agent.py", "w", encoding="utf-8").write(src)
    print("no-args now starts the loop")
import py_compile
py_compile.compile("agent.py", doraise=True)
print("COMPILE-OK")
