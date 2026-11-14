#!/usr/bin/env python3
# sweep.py - budget-steve sweep over griselda's own files (no LLM, no quota)
# scans tasks.json, brain_notes.txt and claim storage for duplicates, stale
# tasks and repeated picks, writes sweep_report.txt and prints the summary.
# pure local file analysis: safe to run anytime, she never sees it.
import json, os, re, difflib, datetime
import sys
NL = chr(10)
HOME = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/griselda-brain")

def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None

def norm(s):
    return re.sub(r"[^a-z0-9 ]+", " ", str(s).lower()).strip()

def sim(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()

report = []
def add(line):
    report.append(line)

# --- tasks.json ---
tasks = load_json(os.path.join(HOME, "tasks.json"))
task_rows = []
if isinstance(tasks, list):
    task_rows = [t for t in tasks if isinstance(t, dict)]
elif isinstance(tasks, dict):
    for v in tasks.values():
        if isinstance(v, list):
            task_rows += [t for t in v if isinstance(t, dict)]
add("TASKS: " + str(len(task_rows)) + " rows")

def task_text(t):
    return str(t.get("task") or t.get("title") or t.get("text") or "").strip()

def task_done(t):
    for k in ("done", "completed", "status"):
        if k in t:
            v = t[k]
            if v is True or (isinstance(v, str) and v.lower() in ("done", "completed", "finished")):
                return True
    return False

def task_age_days(t):
    m = re.search(r"self-(\d{14})", str(t.get("id", "")))
    if m:
        try:
            d = datetime.datetime.strptime(m.group(1), "%Y%m%d%H%M%S")
            return (datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) - d).total_seconds() / 86400.0
        except Exception:
            pass
    for k in ("created", "created_at", "queued", "ts", "time"):
        v = t.get(k)
        if isinstance(v, str):
            m2 = re.search(r"(\d{4})-(\d{2})-(\d{2})", v)
            if m2:
                try:
                    d = datetime.date(int(m2.group(1)), int(m2.group(2)), int(m2.group(3)))
                    return (datetime.date.today() - d).days
                except Exception:
                    pass
    return None

open_tasks = [t for t in task_rows if not task_done(t) and task_text(t)]
# duplicates
groups = []
for t in open_tasks:
    n = norm(task_text(t))
    if not n:
        continue
    placed = False
    for g in groups:
        if sim(n, g[0]) >= 0.8:
            g.append(t)
            placed = True
            break
    if not placed:
        groups.append([n, t])
dup_groups = [g[1:] for g in groups if len(g) > 2]
add("DUPLICATE TASK GROUPS: " + str(len(dup_groups)))
for g in dup_groups[:10]:
    add("  x" + str(len(g)) + ": " + task_text(g[0])[:90])
# stale (3+ days old, not done)
stale = []
for t in open_tasks:
    age = task_age_days(t)
    if age is not None and age >= 3:
        stale.append((age, t))
stale.sort(reverse=True)
add("STALE TASKS (3+ days old, not done): " + str(len(stale)))
for age, t in stale[:10]:
    add("  " + str(int(age)) + "d: " + task_text(t)[:90])
# repeated targets
targets = {}
for t in task_rows:
    tgt = str(t.get("target") or t.get("url") or "").strip()
    if tgt:
        targets[tgt] = targets.get(tgt, 0) + 1
rep = sorted(targets.items(), key=lambda kv: -kv[1])
rep = [(u, c) for u, c in rep if c > 1]
add("REPEATED TARGETS: " + str(len(rep)))
for u, c in rep[:10]:
    add("  x" + str(c) + ": " + u[:90])

# --- brain_notes.txt self-notes ---
self_notes = []
notes_path = os.path.join(HOME, "brain_notes.txt")
if os.path.exists(notes_path):
    with open(notes_path, errors="replace") as f:
        for line in f:
            if "self-note" in line.lower():
                self_notes.append(line.strip())
add("SELF-NOTES: " + str(len(self_notes)))
sn_groups = []
for s in self_notes:
    n = norm(s)
    placed = False
    for g in sn_groups:
        if sim(n, g[0]) >= 0.85:
            g.append(s)
            placed = True
            break
    if not placed:
        sn_groups.append([n, s])
sn_dups = [g[1:] for g in sn_groups if len(g) > 2]
add("REPEATED SELF-NOTES: " + str(len(sn_dups)))
for g in sn_dups[:10]:
    add("  x" + str(len(g)) + ": " + g[0][:90])

# --- claims ---
claims = None
for name in ("claims.json", "saved_claims.json", "claim_ledger.json"):
    p = os.path.join(HOME, name)
    if os.path.exists(p):
        claims = load_json(p)
        add("CLAIMS FILE: " + name)
        break
if claims is None:
    mem = load_json(os.path.join(HOME, "agent_memory.json"))
    if isinstance(mem, dict) and isinstance(mem.get("claims"), (list, dict)):
        claims = mem["claims"]
        add("CLAIMS FILE: agent_memory.json claims key")
if claims is not None:
    rows = claims if isinstance(claims, list) else list(claims.values())
    rows = [c for c in rows if isinstance(c, dict)]
    add("CLAIMS: " + str(len(rows)) + " rows")
    cgroups = []
    for c in rows:
        n = norm(str(c.get("claim") or c.get("text") or ""))
        if not n:
            continue
        placed = False
        for g in cgroups:
            if sim(n, g[0]) >= 0.85:
                g.append(c)
                placed = True
                break
        if not placed:
            cgroups.append([n, c])
    c_dups = [g[1:] for g in cgroups if len(g) > 2]
    add("DUPLICATE CLAIMS: " + str(len(c_dups)))
    for g in c_dups[:10]:
        add("  x" + str(len(g)) + ": " + str(g[0].get("claim", ""))[:90])
else:
    add("CLAIMS: no claims storage found (looked for claims.json, saved_claims.json, claim_ledger.json, agent_memory.json claims key)")

out = NL.join(report)
with open(os.path.join(HOME, "sweep_report.txt"), "w") as f:
    f.write(out + NL)
print(out)
print("full report: ~/griselda-brain/sweep_report.txt")
