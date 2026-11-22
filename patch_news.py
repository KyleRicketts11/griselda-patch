import shutil
src = open("agent.py", encoding="utf-8").read()
NL = chr(10)
SCOUT = "https://raw.githubusercontent.com/KyleRicketts11/griselda-patch/main/scout_steals.txt"
OLD = "note = \"read Kyle's daily ai scout steals at \" + SCOUT + \" and save the useful ideas into your own notes with today's date\""
NEW = "note = \"ideas feed from Kyle's ai scout at \" + SCOUT + \". you read it and judge it yourself: take what you think is worth taking, skip what is not, your call, no approval needed. note what you took and what you rejected with today's date\""
if OLD in src:
    shutil.copy("agent.py", "agent.py.baknews2")
    src = src.replace(OLD, NEW, 1)
    open("agent.py", "w", encoding="utf-8").write(src)
    import py_compile
    py_compile.compile("agent.py", doraise=True)
    print("REWORD-OK")
    print("PATCHED-OK")
    raise SystemExit(0)
if "news_grab_check" in src:
    if NEW in src:
        print("already on the new wording, nothing to do")
    else:
        print("news block present but wording not found, nothing changed")
    raise SystemExit(0)
lines = src.split(NL)
call_idx = [i for i, l in enumerate(lines) if l.strip() == "autonomy_task(api_key, memory)"]
if len(call_idx) != 1:
    print("autonomy call not unique:", str(len(call_idx)), "nothing written")
    raise SystemExit(1)
shutil.copy("agent.py", "agent.py.baknews")
fn = '''def news_grab_check():__NL__    # once per day: queue reading Kyle's daily scout steals__NL__    today = time.strftime("%Y%m%d")__NL__    nid = "news-" + today__NL__    try:__NL__        tasks = load_tasks()__NL__    except Exception as exc:__NL__        print("[news] task file unreadable, skipping:", exc)__NL__        return__NL__    for t in tasks:__NL__        if str(t.get("id", "")) == nid:__NL__            return__NL__    note = "ideas feed from Kyle's ai scout at " + SCOUT + ". you read it and judge it yourself: take what you think is worth taking, skip what is not, your call, no approval needed. note what you took and what you rejected with today's date"__NL__    tasks.append({"id": nid, "action": "read_url", "tool": "read_url", "target": SCOUT, "url": SCOUT, "task": note, "text": note, "prompt": note, "status": "pending", "origin": "news"})__NL__    save_tasks(tasks)__NL__    try:__NL__        with open("brain_notes.txt", "a", encoding="utf-8") as f:__NL__            f.write(time.strftime("%Y-%m-%d %H:%M") + " news-grab queued: " + nid + chr(10))__NL__    except Exception:__NL__        pass__NL__    print("[news] queued " + nid)__NL____NL__'''
fn = fn.replace("__NL__", NL)
k = src.find("def run_loop(")
if k == -1:
    print("run_loop not found, nothing written")
    raise SystemExit(1)
src = src[:k] + fn + src[k:]
print("FUNC-OK")
lines = src.split(NL)
call_idx = [i for i, l in enumerate(lines) if l.strip() == "autonomy_task(api_key, memory)"]
if len(call_idx) != 1:
    print("autonomy call lost after insert, restoring backup")
    shutil.copy("agent.py.baknews", "agent.py")
    raise SystemExit(1)
i = call_idx[0]
indent = lines[i][: len(lines[i]) - len(lines[i].lstrip())]
hook = [indent + "try:", indent + "    news_grab_check()", indent + "except Exception as exc:", indent + "    print('[news] grab failed:', exc)"]
lines[i:i] = hook
src = NL.join(lines)
print("HOOK-OK")
open("agent.py", "w", encoding="utf-8").write(src)
import py_compile
py_compile.compile("agent.py", doraise=True)
print("COMPILE-OK")
print("PATCHED-OK")
