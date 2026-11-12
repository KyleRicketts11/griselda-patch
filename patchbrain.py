#!/usr/bin/env python3
# patchbrain.py - route launch_dashboard.py chat through griselda's real brain loop
# Replaces the mini-brain Gemini call inside chat_brain() with agent.think_and_act,
# so chat gets real tool use (save_claim, read_url) instead of roleplay.
import os, shutil, py_compile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(BASE_DIR, "launch_dashboard.py")
BACKUP = TARGET + ".bakbrain"
NL = chr(10)

START_ANCHOR = '    api_key = os.environ.get("GEMINI_API_KEY")'
END_ANCHOR = '    chat_history.append({"sender": "brain", "text": bot_reply})'

NEW_LINES = [
    '    import agent as _agent',
    '    _key = os.environ.get("GEMINI_API_KEY")',
    '    if _key and len(_key) > 10:',
    '        try:',
    '            hist = [h for h in chat_history[-10:] if h.get("text") and not str(h["text"]).startswith(("Error", "Google is busy", "API Key"))]',
    '            ctx = chr(10).join((("Boss: " if h.get("sender") == "user" else "You: ") + str(h.get("text"))[:200]) for h in hist[:-1][-6:])',
    '            if ctx:',
    '                full = "Recent chat so far:" + chr(10) + ctx + chr(10) + chr(10) + "New message from Boss: " + user_msg',
    '            else:',
    '                full = user_msg',
    '            bot_reply = str(_agent.think_and_act(_key, full))',
    '        except Exception as e:',
    '            bot_reply = "Error processing AI response: " + str(e)',
    '    else:',
    '        bot_reply = "API Key not configured completely yet inside profile environment."',
]


def main():
    if not os.path.exists(TARGET):
        print("ABORT: launch_dashboard.py not found")
        return 1
    src = open(TARGET, "r").read()
    n1 = src.count(START_ANCHOR)
    n2 = src.count(END_ANCHOR)
    if n1 != 1 or n2 != 1:
        print("ABORT: anchors not unique (start=%d end=%d), nothing changed" % (n1, n2))
        return 1
    i1 = src.index(START_ANCHOR)
    i2 = src.index(END_ANCHOR)
    if i2 <= i1:
        print("ABORT: anchors out of order, nothing changed")
        return 1
    gap = src[i1:i2]
    if "def " in gap or "/chat_brain" in gap or "index()" in gap:
        print("ABORT: unexpected code between anchors, nothing changed")
        return 1
    shutil.copy2(TARGET, BACKUP)
    print("backup: " + os.path.basename(BACKUP))
    new_src = src[:i1] + NL.join(NEW_LINES) + NL + src[i2:]
    open(TARGET, "w").write(new_src)
    try:
        py_compile.compile(TARGET, doraise=True)
    except Exception as e:
        shutil.copy2(BACKUP, TARGET)
        print("ABORT: compile failed, backup restored: " + str(e)[:300])
        return 1
    print("compile OK")
    print("launch_dashboard.py: %d -> %d lines" % (len(src.splitlines()), len(new_src.splitlines())))
    print("chat now routes through the real think_and_act loop (tools + save_claim live)")
    print("restart run_unified.py, then ask griselda in chat to save a claim")
    return 0


raise SystemExit(main())
