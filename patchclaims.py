import os, shutil, py_compile

NL = chr(10)
home = os.path.expanduser('~')
p = os.path.join(home, 'griselda-brain', 'agent.py')
src = open(p, encoding='utf-8', errors='replace').read()

if 'save_claim' in src:
    print('already patched, nothing to do')
    raise SystemExit(0)

bak = p + '.bakclaims'
shutil.copy2(p, bak)
print('backup: agent.py.bakclaims')

lines = src.split(NL)
orig_count = len(lines)
fail = []

def find_lines(sub, label):
    hits = [i for i, l in enumerate(lines) if sub in l]
    if len(hits) != 1:
        fail.append(label + ': ' + str(len(hits)) + ' hits')
    return hits

h_rt = find_lines('def run_tool(', 'run_tool def')
h_q = find_lines('"required": ["query"]', 'web_search required line')
h_cond = find_lines('act.get("action") == "read_url"', 'text-JSON condition')
h_name = find_lines('name = "read_url"', 'name assign')
h_args = find_lines('args = {"target": act.get("target") or act.get("url") or ""}', 'args assign')
h_pr = find_lines('decided to use: read_url (json text)', 'print line')
c_sys = src.count('External code runs it and returns the result.')
if c_sys != 1:
    fail.append('system prompt substring: ' + str(c_sys) + ' hits')

if fail:
    print('ABORT, anchor check failed:')
    for x in fail:
        print('  ' + x)
    raise SystemExit(1)

def indent_of(l):
    return l[:len(l) - len(l.lstrip())]

SAVE_FN = [
    'def _save_claim(args):',
    '    import json as _cj',
    '    import time as _ct',
    '    path = os.path.join(BASE_DIR, "claims.json")',
    '    claims = []',
    '    if os.path.exists(path):',
    '        try:',
    '            with open(path, "r", encoding="utf-8") as f:',
    '                claims = _cj.load(f)',
    '            if not isinstance(claims, list):',
    '                claims = []',
    '        except Exception:',
    '            claims = []',
    '    entry = {',
    '        "claim": str(args.get("claim", ""))[:500],',
    '        "source": str(args.get("source", args.get("target", "")))[:200],',
    '        "revealed": str(args.get("revealed", "unknown"))[:80],',
    '        "at": _ct.strftime("%Y-%m-%d %H:%M", _ct.gmtime()),',
    '    }',
    '    claims.append(entry)',
    '    try:',
    '        with open(path, "w", encoding="utf-8") as f:',
    '            _cj.dump(claims, f, ensure_ascii=False, indent=1)',
    '        return "claim saved (" + str(len(claims)) + " total now)"',
    '    except Exception as e:',
    '        return "claim save failed: " + str(e)',
]

SPEC = [
    '{',
    '    "name": "save_claim",',
    '    "description": (',
    '        "Save one canon fact you just learned into the claim ledger. "',
    '        "claim: the fact itself. source: where it came from. "',
    '        "revealed: earliest story point that reveals it, or unknown."',
    '    ),',
    '    "parameters": {',
    '        "type": "object",',
    '        "properties": {',
    '            "claim": {"type": "string"},',
    '            "source": {"type": "string"},',
    '            "revealed": {"type": "string"},',
    '        },',
    '        "required": ["claim"],',
    '    },',
    '},',
]

pr = lines[h_pr[0]]
lines[h_pr[0]] = pr.replace('decided to use: read_url (json text)', 'decided to use: {act.get(' + chr(39) + 'action' + chr(39) + ')} (json text)')
nm = lines[h_name[0]]
lines[h_name[0]] = indent_of(nm) + 'name = act.get(' + chr(39) + 'action' + chr(39) + ')'
cd = lines[h_cond[0]]
lines[h_cond[0]] = cd.replace('act.get("action") == "read_url"', 'act.get("action") in ("read_url", "save_claim")')

jobs = sorted([h_args[0], h_q[0], h_rt[0]], reverse=True)
for idx in jobs:
    if idx == h_args[0]:
        pre = indent_of(lines[idx])
        block = [
            pre + 'if act.get("action") == "save_claim":',
            pre + '    args = dict(act)',
            pre + 'else:',
            pre + '    args = {"target": act.get("target") or act.get("url") or ""}',
        ]
        lines[idx:idx + 1] = block
    elif idx == h_q[0]:
        j = idx + 1
        while j < len(lines) and lines[j].strip() != '},':
            j += 1
        k = j + 1
        if k < len(lines) and lines[k].strip() == '},':
            lines[k + 1:k + 1] = SPEC
        else:
            print('ABORT: web_search spec close not found')
            raise SystemExit(1)
    elif idx == h_rt[0]:
        dl = lines[idx]
        if 'name' not in dl or 'args' not in dl:
            print('ABORT: unexpected run_tool signature: ' + dl.strip())
            raise SystemExit(1)
        di = indent_of(dl)
        guard = [
            di + '    if name == "save_claim":',
            di + '        if not isinstance(args, dict):',
            di + '            args = {"claim": str(args)}',
            di + '        return _save_claim(args)',
        ]
        before = [''] + SAVE_FN + ['']
        lines[idx:idx] = before
        d = idx + len(before)
        lines[d + 1:d + 1] = guard

txt = NL.join(lines)
newtxt = ('External code runs it and returns the result. You may also save a '
          'canon fact you just learned with one JSON line of the same style: '
          '{' + chr(39) + 'action' + chr(39) + ': ' + chr(39) + 'save_claim' + chr(39) + ', '
          + chr(39) + 'claim' + chr(39) + ': the fact, ' + chr(39) + 'source' + chr(39)
          + ': where it came from, ' + chr(39) + 'revealed' + chr(39) + ': story point or unknown}.')
txt = txt.replace('External code runs it and returns the result.', newtxt, 1)

open(p, 'w', encoding='utf-8').write(txt)
try:
    py_compile.compile(p, doraise=True)
    print('compile OK')
except Exception as e:
    shutil.copy2(bak, p)
    print('compile FAILED, backup restored: ' + str(e))
    raise SystemExit(1)

print('agent.py: ' + str(orig_count) + ' -> ' + str(txt.count(NL) + 1) + ' lines')
print('save_claim wired: spec, dispatcher, run_tool, groq prompt')
print('claims.json will live next to brain_notes.txt')
