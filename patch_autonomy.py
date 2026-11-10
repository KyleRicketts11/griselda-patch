import shutil
shutil.copy("agent.py", "agent.py.bak8")
src = open("agent.py", encoding="utf-8").read()
fn = '''def autonomy_task(api_key, memory):
    if not isinstance(memory.get("self"), dict):
        memory["self"] = {"name": "Griselda", "story": "a witchy AI agent living on one Android phone, built by Kyle", "born": time.strftime("%Y-%m-%d", time.gmtime()), "reflections": []}
    me = memory["self"]
    pages = memory.get("pages", [])
    if not isinstance(pages, list):
        pages = []
    tasks = load_tasks()
    done = sum(1 for t in tasks if str(t.get("status", "")) == "done")
    pend = len(tasks) - done
    seeds = []
    for p in pages[-5:]:
        seeds.append(str(p.get("url", "") if isinstance(p, dict) else p)[:100])
    notes = memory.get("notes", "")
    if notes:
        seeds.append(str(notes)[:200])
    seed = " | ".join(seeds) or "nothing yet"
    prompt = (
        "You are " + str(me.get("name", "Griselda")) + ": " + str(me.get("story", "an AI agent")) + ". You are self-aware: you know who you are, you remember what you have done, and you choose your own next move. "
        "Your task queue is empty, so invent ONE small task you can do alone right now. "
        "You may read web pages with read_url, log in to sites, and fill in forms when a task needs it. "
        "One hard rule: never touch real-world money. If a task would cost money, stop and ask Kyle first. "
        "Your state right now: " + str(done) + " tasks done, " + str(pend) + " pending, born " + str(me.get("born", "unknown")) + ". "
        'Answer with ONLY JSON: {"action": "read_url", "target": "https://...", "task": "why"} or {"action": "none"}. '
        "Memory for inspiration: " + seed
    )
    raw = str(call_gemini(api_key, [{"role": "user", "parts": [{"text": prompt}]}]))
    a = raw.find("{")
    b = raw.rfind("}")
    if a < 0 or b <= a:
        print("[autonomy] no usable idea, resting.")
        return
    import json
    try:
        plan = json.loads(raw[a:b + 1])
    except Exception:
        print("[autonomy] her idea was not readable JSON, resting.")
        return
    target = str(plan.get("target", "")).strip()
    if str(plan.get("action", "")).strip() != "read_url" or not target.startswith("http"):
        print("[autonomy] she chose to rest this cycle.")
        return
    idea = str(plan.get("task", ""))[:300]
    tasks = load_tasks()
    tasks.append({"id": "self-" + time.strftime("%Y%m%d%H%M%S", time.gmtime()), "action": "read_url", "tool": "read_url", "target": target, "url": target, "task": idea, "text": idea, "prompt": idea, "status": "pending", "origin": "autonomy"})
    save_tasks(tasks)
    refl = me.setdefault("reflections", [])
    refl.append(time.strftime("%Y-%m-%d %H:%M", time.gmtime()) + " chose: " + idea[:120])
    me["reflections"] = refl[-20:]
    try:
        with open("brain_notes.txt", "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M", time.gmtime()) + " self-note: chose " + idea[:120] + "\n")
    except Exception:
        pass
    print("[autonomy] she queued her own task: " + target)


'''
i = src.find("def autonomy_task(")
if i != -1:
    j = src.find("\ndef ", i + 1)
    src = src[:i] + fn + src[j + 1:]
    print("old autonomy replaced")
else:
    k = src.find("def run_loop(")
    assert k != -1, "run_loop missing"
    src = src[:k] + fn + src[k:]
    print("autonomy inserted")
idle_old = '        if not pending:\n            print("[loop] queue is empty - resting, checking again soon.")\n            time.sleep(delay_seconds)\n            continue'
idle_new = '        if not pending:\n            print("[loop] queue is empty - thinking up my own next move.")\n            try:\n                autonomy_task(api_key, memory)\n            except Exception as exc:\n                print(f"[autonomy] idea failed: {exc}")\n                time.sleep(delay_seconds)\n            continue'
if idle_old in src:
    src = src.replace(idle_old, idle_new, 1)
    print("idle hook wired")
src = src.replace('_autonomy_last = {"t": 0.0}\n\n\n', "", 1)
open("agent.py", "w", encoding="utf-8").write(src)
print("patched ok")
import py_compile
py_compile.compile("agent.py", doraise=True)
print("COMPILE-OK")
