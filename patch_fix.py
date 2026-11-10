import shutil
shutil.copy("agent.py", "agent.py.bak9")
src = open("agent.py", encoding="utf-8").read()
nl = chr(10)
good = 'f.write(time.strftime("%Y-%m-%d %H:%M", time.gmtime()) + " self-note: chose " + idea[:120] + chr(10))'
bad1 = 'f.write(time.strftime("%Y-%m-%d %H:%M", time.gmtime()) + " self-note: chose " + idea[:120] + "' + nl + '")'
bad2 = 'f.write(time.strftime("%Y-%m-%d %H:%M", time.gmtime())) + " self-note: chose " + idea[:120] + "' + nl + '")'
if bad1 in src:
    src = src.replace(bad1, good, 1)
    print("self-note line repaired (shape 1)")
elif bad2 in src:
    src = src.replace(bad2, good, 1)
    print("self-note line repaired (shape 2)")
else:
    i = src.find("self-note: chose ")
    print("exact shape not found, showing the area:")
    print(src[max(0, i - 200):i + 160])
    raise SystemExit(1)
open("agent.py", "w", encoding="utf-8").write(src)
import py_compile
py_compile.compile("agent.py", doraise=True)
print("COMPILE-OK")
