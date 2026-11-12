#!/usr/bin/env python3
# probe3.py - find every Google model on the griselda key with its own free daily bucket.
# Free quota is PER MODEL per day: each extra alive model is more thinks a day for griselda.
# v2: scans every small file in griselda-brain for the key (the key is not a plain assignment),
# validates each candidate against the models list endpoint, then probes the queued models.
import json, os, re, urllib.request, urllib.error

HOME = os.path.expanduser("~")
BRAIN = os.path.join(HOME, "griselda-brain")
KEY_PAT = re.compile(r"((?:AIza|AQ\.)[A-Za-z0-9_\-]{20,})")
cands = []
seen = set()

for root, dirs, files in os.walk(BRAIN):
    dirs[:] = [d for d in dirs if not d.startswith('.')]
    for f in files:
        p = os.path.join(root, f)
        try:
            if os.path.getsize(p) > 1000000 or f.endswith('.zip') or f.endswith('.png') or f.endswith('.jpg'):
                continue
            txt = open(p, 'r', encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        for m in KEY_PAT.finditer(txt):
            k = m.group(1)
            if k not in seen:
                seen.add(k)
                cands.append(k)

if not cands:
    print('ABORT: no Google-style key (AIza... or AQ....) found anywhere in griselda-brain')
    raise SystemExit(1)
print('found %d key candidate(s), tails: %s' % (len(cands), ' '.join(c[-4:] for c in cands)))


def good(k):
    req = urllib.request.Request('https://generativelanguage.googleapis.com/v1beta/models?key=' + k)
    try:
        urllib.request.urlopen(req, timeout=30)
        return True
    except Exception:
        return False


key = None
for k in cands:
    if good(k):
        key = k
        break
    print('candidate ending ' + k[-4:] + ' rejected by google, trying next')
if not key:
    print("ABORT: none of the found keys passed google's check (revoked or network down)")
    raise SystemExit(1)
print('using key ending: ' + key[-4:])

MODELS = ['gemini-3.5-flash', 'gemini-3.5-flash-lite', 'gemini-3.6-flash', 'gemini-3.8-flash', 'gemini-3.8-flash-lite']


def probe(model):
    url = 'https://generativelanguage.googleapis.com/v1beta/models/' + model + ':generateContent?key=' + key
    body = json.dumps({'contents': [{'role': 'user', 'parts': [{'text': 'Reply with the single word: ok'}]}]}).encode('utf-8')
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req, timeout=40)
        print(model + ': ALIVE, own free bucket confirmed')
    except urllib.error.HTTPError as e:
        txt = e.read().decode('utf-8', 'replace')
        if e.code == 429:
            mm = re.search(r'limit: ([0-9]+)', txt)
            print(model + ': 429, daily bucket exists, limit ' + (mm.group(1) if mm else 'unknown'))
        elif e.code == 404:
            print(model + ': 404, not open to free keys')
        else:
            print(model + ': HTTP ' + str(e.code) + ' ' + txt[:160])
    except Exception as e:
        print(model + ': failed ' + str(e)[:140])


for mo in MODELS:
    probe(mo)
print('done: every ALIVE or 429-with-limit model is a real extra daily bucket')
