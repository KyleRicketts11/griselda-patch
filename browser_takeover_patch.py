import os, shutil, sys, py_compile

HOME = os.path.expanduser('~')
P = os.path.join(HOME, 'griselda-brain', 'launch_dashboard.py')
src = open(P).read()

if "route('/her_state')" in src:
    print('already patched, nothing to do')
    sys.exit(0)

shutil.copyfile(P, P + '.baktakeover')
NL = chr(10)
lines = src.split(NL)

si = None
for i, l in enumerate(lines):
    if l.strip().startswith("@app.route('/shot')"):
        si = i
        break
if si is None:
    print('PATCH FAILED: /shot route not found. nothing changed.')
    sys.exit(1)

state = [
    "@app.route('/her_state')",
    "def her_state():",
    "    import os, json",
    "    from flask import jsonify",
    "    home = os.path.expanduser('~')",
    "    url = ''",
    "    try:",
    "        with open(os.path.join(home, 'griselda-brain', 'tasks.json')) as f:",
    "            data = json.load(f)",
    "        tasks = data if isinstance(data, list) else data.get('tasks', [])",
    "        for t in reversed(tasks):",
    "            tgt = ''",
    "            if isinstance(t, dict):",
    "                tgt = str(t.get('target', ''))",
    "                if not tgt.startswith('http'):",
    "                    for tok in str(t.get('task', '')).split():",
    "                        if tok.startswith('http'):",
    "                            tgt = tok",
    "            if tgt.startswith('http'):",
    "                url = tgt",
    "                break",
    "    except Exception:",
    "        pass",
    "    if not url:",
    "        try:",
    "            with open(os.path.join(home, 'griselda-brain', 'brain_notes.txt')) as f:",
    "                txt = f.read()",
    "            urls = [w for w in txt.split() if w.startswith('http')]",
    "            if urls:",
    "                u = urls[-1]",
    "                for ch in [')', '>', '<', ',']:",
    "                    u = u.replace(ch, '')",
    "                url = u",
    "        except Exception:",
    "            pass",
    "    return jsonify(url=url)",
    "",
]
lines[si:si] = state
src2 = NL.join(lines)

i3 = src2.find("<!-- Tab 3: Browser Tab -->")
d = src2.find("<div", i3)
de = src2.find(">", d) + 1
if i3 == -1 or d == -1 or de <= 0:
    print('PATCH FAILED: browser pane not found. nothing changed.')
    sys.exit(1)

strip = [
    '<div id="takeover_strip" style="margin:8px 0 12px 0;padding:10px;background:#16181d;border:1px solid #2a2d35;border-radius:10px">',
    '  <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:8px">',
    '    <span id="her_url" style="color:#8ab4f8;font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:65%">her page: ...</span>',
    '    <button id="takeover_btn" style="background:#f0b429;color:#111;border:0;border-radius:6px;padding:8px 12px;font-weight:bold;white-space:nowrap">Take over</button>',
    '  </div>',
    '  <img id="her_shot" src="/shot" style="width:100%;border-radius:8px;background:#111;display:block">',
    '</div>',
    '<script>',
    '(function(){',
    '  var img = document.getElementById("her_shot");',
    '  var lab = document.getElementById("her_url");',
    '  var herUrl = "";',
    '  function tick(){',
    '    img.src = "/shot?t=" + Date.now();',
    '    fetch("/her_state").then(function(r){return r.json()}).then(function(d){',
    '      if(d.url){ lab.textContent = "her page: " + d.url; herUrl = d.url; }',
    '      else { lab.textContent = "her page: none yet"; herUrl = ""; }',
    '    }).catch(function(){});',
    '  }',
    '  tick();',
    '  setInterval(tick, 5000);',
    '  document.getElementById("takeover_btn").addEventListener("click", function(){',
    '    if(herUrl){ window.open(herUrl, "_blank"); }',
    '  });',
    '})();',
    '</script>',
]
strip_text = NL.join(strip) + NL
out = src2[:de] + strip_text + src2[de:]

open(P, 'w').write(out)
try:
    py_compile.compile(P, doraise=True)
    print('PATCH LANDED: browser tab now shows her live screen, her page url, and a Take over button that opens her page in your browser. restart run_unified to see it.')
except Exception as e:
    shutil.copyfile(P + '.baktakeover', P)
    print('PATCH FAILED: ' + str(e) + ' backup restored, nothing broken.')
