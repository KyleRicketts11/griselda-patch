import os, shutil, sys, py_compile

HOME = os.path.expanduser('~')
P = os.path.join(HOME, 'griselda-brain', 'launch_dashboard.py')

src = open(P).read()

if "route('/live')" in src or "route(\"/live\")" in src:
    print('already patched, nothing to do')
    sys.exit(0)

lines = src.split(chr(10))

idx = None
for i, l in enumerate(lines):
    if l.strip().startswith("@app.route('/')"):
        idx = i
        break

if idx is None:
    print('anchor not found, no change made')
    sys.exit(1)

block = [
    "@app.route('/shot')",
    "def live_shot():",
    "    import os",
    "    from flask import send_file",
    "    shot = os.path.join(os.path.expanduser('~'), 'griselda-brain', 'last_shot.png')",
    "    if os.path.exists(shot):",
    "        return send_file(shot, mimetype='image/png')",
    "    return '(no screenshot yet)', 404",
    "",
    "@app.route('/live')",
    "def live_view():",
    "    import os, time, html",
    "    notes = '(no notes yet)'",
    "    try:",
    "        with open(os.path.join(os.path.expanduser('~'), 'griselda-brain', 'brain_notes.txt')) as f:",
    "            notes = ''.join(f.readlines()[-20:])",
    "    except Exception:",
    "        pass",
    "    page = '<!doctype html><html><head><meta charset=utf-8><meta http-equiv=refresh content=8><title>griselda live</title><style>body{background:#111;color:#eee;font-family:monospace;padding:12px}img{width:100%;border:1px solid #333;border-radius:8px}pre{white-space:pre-wrap;color:#9f9;font-size:12px;line-height:1.5}</style></head><body><h3>her last seen page</h3><img src=/shot?' + str(int(time.time())) + '><h3>her recent actions</h3><pre>' + html.escape(notes) + '</pre></body></html>'",
    "    return page",
    "",
]

lines[idx:idx] = block
out = chr(10).join(lines)
shutil.copyfile(P, P + '.baklive')
open(P, 'w').write(out)
py_compile.compile(P, doraise=True)
print('patched ok: dashboard now serves /live (latest screenshot + recent actions) and /shot')
