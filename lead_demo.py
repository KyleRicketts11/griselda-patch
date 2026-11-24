#!/usr/bin/env python3
# lead_demo.py - sellable-skill demo for griselda-brain (standalone, touches nothing of hers)
# A fake customer lead comes in; her brain (same Gemini setup) drafts the follow-up
# reply a small business would text back. Draft saved to lead_demo_draft.txt.
import glob, json, os, re, sys, urllib.request, urllib.error

BASE = os.path.expanduser("~/griselda-brain")
LEAD = "Hi, I found you on Google. My water heater started leaking last night and water is spreading into the hallway closet. I am in Medford. How fast can someone come out and what would it cost?"
PROMPT = ("You are the front-desk assistant for Willow Plumbing and Heating, a small local shop. "
          "A customer just texted: " + chr(34) + LEAD + chr(34) + " "
          "Draft the exact text-message reply to send them. Requirements: confirm you got it and you are sorry about the mess, "
          "ask exactly two things needed to book them (their address and a good window today), "
          "mention the emergency visit starts with an $89 diagnostic fee, keep it warm and under 80 words, no emojis. "
          "Reply with only the message text, nothing else.")

def find_key():
    env = os.environ.get("GEMINI_API_KEY")
    if env:
        return env
    for f in glob.glob(os.path.join(BASE, "*.key")):
        try:
            t = open(f, encoding="utf-8", errors="ignore").read().strip()
        except Exception:
            continue
        if t.startswith("AIza"):
            return t
    for f in glob.glob(os.path.join(BASE, "*")):
        if not os.path.isfile(f):
            continue
        if os.path.basename(f) in ("lead_demo.py", "runeval.py", "tasks.json", "brain_notes.txt", "eval_history.jsonl"):
            continue
        if os.path.getsize(f) > 500000:
            continue
        try:
            t = open(f, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        m = re.search(r"AIza[0-9A-Za-z_-]{30,}", t)
        if m:
            return m.group(0)
    return None

def pick_model():
    p = os.path.join(BASE, "models.txt")
    try:
        for l in open(p, encoding="utf-8"):
            l = l.strip()
            if l and not l.startswith("#"):
                return l
    except Exception:
        pass
    return "gemini-3.5-flash"

def main():
    key = find_key()
    if not key:
        print("NO-KEY: could not find a Gemini key (looked at $GEMINI_API_KEY, *.key files, and her own files)")
        return 1
    model = pick_model()
    url = "https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent?key=" + key
    body = json.dumps({"contents": [{"parts": [{"text": PROMPT}]}]}).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print("MODEL-ERROR", e.code, e.read().decode("utf-8", "ignore")[:300])
        return 1
    except Exception as e:
        print("MODEL-ERROR", str(e)[:300])
        return 1
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        print("UNEXPECTED-RESPONSE", json.dumps(data)[:300])
        return 1
    out = os.path.join(BASE, "lead_demo_draft.txt")
    open(out, "w", encoding="utf-8").write("LEAD: " + LEAD + chr(10) + chr(10) + "GRISELDA'S REPLY:" + chr(10) + text + chr(10))
    print(text)
    print("")
    print("saved to " + out)
    return 0

sys.exit(main())
