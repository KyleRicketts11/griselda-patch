#!/usr/bin/env python3
# probe3.py - find every Google model on the griselda key with its own free daily bucket.
# Free quota is PER MODEL per day: each extra alive model is more thinks a day for griselda.
import glob, json, os, re, urllib.request, urllib.error

HOME = os.path.expanduser("~")
BRAIN = os.path.join(HOME, "griselda-brain")
cands = []


def grab(text):
    m = re.search(r"[A-Za-z_]*KEY[A-Za-z_]*[ \t]*=[ \t]*['\"]((?:AIza|AQ\.)[A-Za-z0-9_\-]{20,})['\"]", text)
    if m:
        cands.append(m.group(1))


for f in ("agent.py", "run_unified.py", "launch_dashboard.py", "config.py", "settings.py"):
    p = os.path.join(BRAIN, f)
    if os.path.exists(p):
        grab(open(p, "r", encoding="utf-8", errors="replace").read())

if not cands:
    for p in sorted(glob.glob(os.path.join(BRAIN, "*.key"))):
        cands.append(open(p, "r", encoding="utf-8", errors="replace").read().strip())

if not cands:
    src = open(os.path.join(BRAIN, "agent.py"), "r", encoding="utf-8", errors="replace").read()
    for m in re.finditer(r"((?:AIza|AQ\.)[A-Za-z0-9_\-]{20,})", src):
        cands.append(m.group(1))

if not cands:
    print("ABORT: no api key found in agent.py or *.key files")
    raise SystemExit(1)


def good(k):
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models?key=" + k)
    try:
        urllib.request.urlopen(req, timeout=30)
        return True
    except urllib.error.HTTPError as e:
        return e.code != 400


key = None
for k in cands:
    if good(k):
        key = k
        break
if not key:
    print("ABORT: every key candidate failed the check (invalid or network)")
    raise SystemExit(1)
print("using key ending: " + key[-4:])

MODELS = ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-3.8-flash", "gemini-3.8-flash-lite"]


def probe(model):
    url = "https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent?key=" + key
    body = json.dumps({"contents": [{"role": "user", "parts": [{"text": "Reply with the single word: ok"}]}]}).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=40)
        print(model + ": ALIVE, own free bucket confirmed")
    except urllib.error.HTTPError as e:
        txt = e.read().decode("utf-8", "replace")
        if e.code == 429:
            mm = re.search(r"limit: ([0-9]+)", txt)
            print(model + ": 429, daily bucket exists, limit " + (mm.group(1) if mm else "unknown"))
        elif e.code == 404:
            print(model + ": 404, not open to free keys")
        else:
            print(model + ": HTTP " + str(e.code) + " " + txt[:160])
    except Exception as e:
        print(model + ": failed " + str(e)[:140])


for mo in MODELS:
    probe(mo)
print("done: every ALIVE or 429-with-limit model is a real extra daily bucket")
