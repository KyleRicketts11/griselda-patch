#!/usr/bin/env python3
# proof_watch.py - visible proof griselda is acting: watches her task list and
# pops a real Android toast on Kyle's screen every time she queues a task or
# finishes one. Runs beside her, never touches agent.py or her files.
import json, os, subprocess, time

BASE = os.path.expanduser("~/griselda-brain")
TASKS = os.path.join(BASE, "tasks.json")
SEEN = {}

def toast(msg):
    try:
        subprocess.run(["termux-toast", "-g", "top", msg], timeout=15)
    except Exception:
        pass

def load():
    try:
        with open(TASKS) as f:
            data = json.load(f)
    except Exception:
        return []
    if isinstance(data, dict):
        for key in ("tasks", "queue", "items"):
            if isinstance(data.get(key), list):
                return data[key]
        return []
    if isinstance(data, list):
        return data
    return []

def label(t):
    parts = []
    for k in ("task", "action", "cmd", "target", "url"):
        v = t.get(k)
        if v:
            parts.append(str(v))
    return " ".join(parts)[:70] or "a task"

def sweep():
    fired = []
    for t in load():
        if not isinstance(t, dict):
            continue
        tid = str(t.get("id") or "")
        if not tid:
            continue
        st = str(t.get("status") or "")
        prev = SEEN.get(tid)
        if prev is None:
            SEEN[tid] = st
            if st and st != "done":
                fired.append("griselda queued: " + label(t))
            continue
        if st != prev:
            SEEN[tid] = st
            if st == "done":
                fired.append("griselda did it: " + label(t))
    if len(SEEN) > 400:
        keep = list(SEEN.items())[-200:]
        SEEN.clear()
        SEEN.update(keep)
    return fired

if __name__ == "__main__":
    print("proof watch up: griselda's moves will toast on your screen")
    while True:
        for m in sweep():
            toast(m)
        time.sleep(4)
