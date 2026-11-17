import sys, py_compile

P = "/data/data/com.termux/files/home/griselda-brain/agent.py"

src = open(P).read()

if "browser.md" in src:
    print("already patched, nothing to do")
    sys.exit(0)

lines = src.split(chr(10))

idx = None
for i, l in enumerate(lines):
    if l.strip().startswith("GRISELDA_SYSTEM = ("):
        idx = i
        break

if idx is None:
    print("anchor not found, no change made")
    sys.exit(1)

end = None
for j in range(idx + 1, len(lines)):
    if lines[j].strip() == ")":
        end = j
        break

if end is None:
    print("closing paren not found, no change made")
    sys.exit(1)

ins = [
    "try:",
    "    _browser_rules = open(\"/data/data/com.termux/files/home/griselda-brain/browser.md\").read()",
    "    GRISELDA_SYSTEM = GRISELDA_SYSTEM + chr(10) + \"BROWSER RULES, follow these for every read_url or browsing task:\" + chr(10) + _browser_rules",
    "except Exception:",
    "    pass",
]

lines[end + 1:end + 1] = ins
out = chr(10).join(lines)
open(P, "w").write(out)
py_compile.compile(P, doraise=True)
print("patched ok: GRISELDA_SYSTEM now loads browser.md at startup")
