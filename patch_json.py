import shutil
shutil.copy("agent.py", "agent.py.bak11")
src = open("agent.py", encoding="utf-8").read()
nl = chr(10)
j = src.find("her idea was not readable JSON")
if j == -1:
    print("autonomy block not found")
    raise SystemExit(1)
m = src.rfind("import json", 0, j)
r = src.rfind("raw = str(call_gemini", 0, m)
if m == -1 or r == -1:
    print("block start not found")
    raise SystemExit(1)
ls = src.rfind(nl, 0, r) + 1
k = src.find("return", j)
end = src.find(nl, k) + 1
new_lines = [
    "    import json",
    "    plan = None",
    "    for _try in range(3):",
    '        raw = str(call_gemini(api_key, [{"role": "user", "parts": [{"text": prompt}]}]))',
    '        raw = raw.replace("```json", " ").replace("```", " ")',
    '        a = raw.find("{")',
    '        b = raw.rfind("}")',
    "        if a < 0 or b <= a:",
    '            print("[autonomy] no usable idea this try, retrying.")',
    "            time.sleep(5)",
    "            continue",
    "        try:",
    "            plan = json.loads(raw[a:b + 1])",
    "            break",
    "        except Exception:",
    '            print("[autonomy] idea not readable this try, retrying.")',
    "            time.sleep(5)",
    "    if plan is None:",
    '        print("[autonomy] she could not form a clean idea, resting this cycle.")',
    "        return",
]
src = src[:ls] + nl.join(new_lines) + nl + src[end:]
open("agent.py", "w", encoding="utf-8").write(src)
print("autonomy retries wired")
import py_compile
py_compile.compile("agent.py", doraise=True)
print("COMPILE-OK")
