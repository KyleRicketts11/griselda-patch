import shutil
shutil.copy("agent.py", "agent.py.bak12")
src = open("agent.py", encoding="utf-8").read()
nl = chr(10)
j = src.find("no usable idea this try")
if j == -1:
    print("autonomy retry block not found")
    raise SystemExit(1)
r = src.rfind("raw = str(call_gemini", 0, j)
if r == -1:
    print("call line not found")
    raise SystemExit(1)
ls = src.rfind(nl, 0, r) + 1
le = src.find(nl, r) + 1
new_lines = [
    "        try:",
    '            raw = str(call_gemini(api_key, [{"role": "user", "parts": [{"text": prompt}]}]))',
    "        except Exception:",
    '            print("[autonomy] gemini is busy this try, retrying.")',
    "            time.sleep(15)",
    "            continue",
]
src = src[:ls] + nl.join(new_lines) + nl + src[le:]
open("agent.py", "w", encoding="utf-8").write(src)
print("503 shield wired")
import py_compile
py_compile.compile("agent.py", doraise=True)
print("COMPILE-OK")
