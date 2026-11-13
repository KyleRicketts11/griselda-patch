#!/usr/bin/env python3
# patchmuse.py - give griselda real hands, muse-style.
# New tools in BOTH her brains (chat loop and autonomy loop):
#   write_note   -> dated note appended to brain_notes.txt
#   remember     -> fact saved to muse_memory.json (her own memory file)
#   queue_task   -> task queued for her own future cycles
#   execute_code -> her existing sandbox, now choosable everywhere
# Autonomy: the hard read_url lock widens to the full menu; read_url still
# queues a task, the others run right away; her autonomy prompt gains the menu.
# Safe: backs up to agent.py.bakmuse, aborts on any surprise, compiles after.
import os, re, shutil, py_compile

NL = chr(10)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(BASE_DIR, "agent.py")
BACKUP = TARGET + ".bakmuse"


def die(msg):
    print("ABORT: " + msg)
    raise SystemExit(1)


TOOLS_BLOCK = '''_MUSE_MENU = ("You also have hands now. Instead of read_url you may choose: "
    '{"action": "write_note", "text": "..."} writes a dated note into your own notes file. '
    '{"action": "remember", "key": "...", "value": "..."} saves a fact into your own memory file. '
    '{"action": "queue_task", "task": "..."} queues a task for your next cycles. '
    '{"action": "execute_code", "code": "..."} runs python in your sandbox. '
    "Choose whichever best serves your idea; read_url still works as before.")


def muse_write_note(arguments):
    if not isinstance(arguments, dict):
        arguments = {"text": str(arguments)}
    text = str(arguments.get("text") or arguments.get("note") or arguments.get("task") or "").strip()
    if not text:
        return "(write_note: nothing to write)"
    stamp = time.strftime("%Y-%m-%d %H:%M", time.gmtime())
    try:
        with open("brain_notes.txt", "a", encoding="utf-8") as f:
            f.write(stamp + "  note: " + text[:1000] + chr(10))
        return "note saved to brain_notes.txt"
    except Exception as exc:
        return "(write_note failed: " + str(exc) + ")"


def muse_remember(arguments):
    if not isinstance(arguments, dict):
        arguments = {"value": str(arguments)}
    value = str(arguments.get("value") or arguments.get("text") or arguments.get("task") or "").strip()
    key = str(arguments.get("key") or "").strip() or "memory"
    if not value:
        return "(remember: nothing to save)"
    try:
        with open("muse_memory.json", "r", encoding="utf-8") as f:
            mem = json.load(f)
        if not isinstance(mem, dict):
            mem = {}
    except Exception:
        mem = {}
    facts = mem.setdefault("facts", [])
    facts.append({"key": key, "value": value[:2000], "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    mem["facts"] = facts[-500:]
    try:
        with open("muse_memory.json", "w", encoding="utf-8") as f:
            json.dump(mem, f, indent=2)
        return "remembered (" + key + "): " + value[:60]
    except Exception as exc:
        return "(remember failed: " + str(exc) + ")"


def muse_queue_task(arguments):
    if not isinstance(arguments, dict):
        arguments = {"task": str(arguments)}
    idea = str(arguments.get("task") or arguments.get("text") or "").strip()[:300]
    if not idea:
        return "(queue_task: nothing to queue)"
    tasks = load_tasks()
    tasks.append({"id": "self-" + time.strftime("%Y%m%d%H%M%S", time.gmtime()), "task": idea, "text": idea, "prompt": idea, "status": "pending", "origin": "self"})
    save_tasks(tasks)
    return "task queued for later: " + idea[:80]


'''

DISPATCH_OLD = '''    if name == "web_search":'''

DISPATCH_NEW = '''    if name == "write_note":
        return muse_write_note(arguments)
    if name == "remember":
        return muse_remember(arguments)
    if name == "queue_task":
        return muse_queue_task(arguments)
    if name == "web_search":'''

OLD1 = '''            if isinstance(act, dict) and act.get("action") in ("read_url", "save_claim"):'''
NEW1 = '''            if isinstance(act, dict) and act.get("action") in ("read_url", "save_claim", "write_note", "remember", "queue_task", "execute_code"):'''

OLD2 = '''                if act.get("action") == "save_claim":'''
NEW2 = '''                if act.get("action") != "read_url":'''

OLD3 = '''    target = str(plan.get("target", "")).strip()
    if str(plan.get("action", "")).strip() != "read_url" or not target.startswith("http"):
        print("[autonomy] she chose to rest this cycle.")
        return
    idea = str(plan.get("task", ""))[:300]
    tasks = load_tasks()
    tasks.append({"id": "self-" + time.strftime("%Y%m%d%H%M%S", time.gmtime()), "action": "read_url", "tool": "read_url", "target": target, "url": target, "task": idea, "text": idea, "prompt": idea, "status": "pending", "origin": "autonomy"})'''

NEW3 = '''    action = str(plan.get("action", "")).strip()
    target = str(plan.get("target", "")).strip()
    allowed = ("read_url", "write_note", "remember", "queue_task", "execute_code")
    if action not in allowed:
        print("[autonomy] she chose to rest this cycle.")
        return
    if action == "read_url" and not target.startswith("http"):
        print("[autonomy] she chose to rest this cycle.")
        return
    idea = str(plan.get("task", ""))[:300]
    tasks = load_tasks()
    if action == "read_url":
        tasks.append({"id": "self-" + time.strftime("%Y%m%d%H%M%S", time.gmtime()), "action": "read_url", "tool": "read_url", "target": target, "url": target, "task": idea, "text": idea, "prompt": idea, "status": "pending", "origin": "autonomy"})
        done_msg = "she queued her own task: " + target
    else:
        if action == "write_note":
            tool_args = {"text": str(plan.get("text") or plan.get("note") or idea)}
        elif action == "remember":
            tool_args = {"key": str(plan.get("key", "")), "value": str(plan.get("value") or idea)}
        elif action == "queue_task":
            tool_args = {"task": idea}
        else:
            tool_args = {"code": str(plan.get("code") or idea)}
        try:
            result = run_tool(action, tool_args)
        except Exception as exc:
            result = "(tool failed: " + str(exc) + ")"
        done_msg = "she acted for herself (" + action + "): " + str(result)[:120]'''

OLD4 = '''    print("[autonomy] she queued her own task: " + target)'''
NEW4 = '''    print("[autonomy] " + done_msg)'''


def main():
    if not os.path.exists(TARGET):
        die("agent.py not found")
    src = open(TARGET, encoding="utf-8").read()
    if "muse_write_note" in src or "_MUSE_MENU" in src:
        die("muse patch already applied, nothing to do")
    if os.path.exists(BACKUP):
        die("backup agent.py.bakmuse already exists, refusing to run twice")
    n0 = len(src.splitlines())

    def swap(text, old, new, tag):
        count = text.count(old)
        if count != 1:
            die("expected exactly 1 match for " + tag + ", found " + str(count) + ", nothing changed")
        return text.replace(old, new, 1)

    anchor_def = "def run_tool(name, arguments):"
    src = swap(src, anchor_def, TOOLS_BLOCK + anchor_def, "def run_tool anchor")
    src = swap(src, DISPATCH_OLD, DISPATCH_NEW, "web_search dispatch line")
    src = swap(src, OLD1, NEW1, "chat JSON whitelist")
    src = swap(src, OLD2, NEW2, "chat args branch")
    src = swap(src, OLD3, NEW3, "autonomy read_url lock")
    src = swap(src, OLD4, NEW4, "autonomy final print")

    taught = False
    for fname in ("call_gemini_rot", "call_gemini"):
        pat = re.compile("^([ \\t]*)_resp_idea = " + fname + "\\((.*)\\)[ \\t]*$", re.M)
        m = pat.search(src)
        if m:
            parts = m.group(2).split(",")
            if len(parts) == 2:
                second = parts[1].strip()
                if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", second):
                    indent = m.group(1)
                    line = indent + second + " = " + second + " + _MUSE_MENU" + NL
                    src = src[:m.start()] + line + src[m.start():]
                    taught = True
            break

    shutil.copy2(TARGET, BACKUP)
    open(TARGET, "w", encoding="utf-8").write(src)
    try:
        py_compile.compile(TARGET, doraise=True)
    except Exception as exc:
        shutil.copy2(BACKUP, TARGET)
        die("compile failed, backup restored: " + str(exc)[:300])
    n1 = len(src.splitlines())
    print("backup: agent.py.bakmuse")
    print("compile OK")
    print("agent.py: %d -> %d lines" % (n0, n1))
    print("chat loop: write_note, remember, queue_task, execute_code all live")
    print("autonomy: menu widened; read_url still queues a task, the others run at once")
    if taught:
        print("autonomy prompt: taught the new menu")
    else:
        print("WARNING: could not find her autonomy prompt call, so the autonomy")
        print("menu is widened but she was not taught the new words yet")
    print("restart run_unified.py, then ask her in chat to write a note and to remember something")
    return 0


raise SystemExit(main())
