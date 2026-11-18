import shutil, sys
P = "/data/data/com.termux/files/home/griselda-brain/launch_dashboard.py"
s = open(P, encoding="utf-8").read()
if 'data-bs-target="#live"' in s:
    print("ALREADY PATCHED: live tab already in her dashboard. nothing to do.")
    sys.exit(0)
shutil.copy2(P, P + ".baklivetab")
NL = chr(10)
i = s.find('data-bs-target="#toes"')
j = s.find("</li>", i)
k = s.find("<!-- Tab 4: Wally's Toes -->")
if i == -1 or j == -1 or k == -1:
    print("PATCH FAILED: anchors missing. nothing changed.")
    sys.exit(1)
pane = ('            <!-- Tab 5: Live view -->' + NL +
        '            <div class="tab-pane fade" id="live">' + NL +
        '              <iframe src="/live" style="width:100%;height:85vh;border:0;border-radius:10px;background:#0b0b0e"></iframe>' + NL +
        '            </div>' + NL + NL)
s = s[:k] + pane + s[k:]
nav = NL + '            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#live" type="button">📸 Live</button></li>'
s = s[:j+len("</li>")] + nav + s[j+len("</li>"):]
open(P, "w", encoding="utf-8").write(s)
print("PATCH LANDED: live tab added next to toes. restart run_unified to see it. undo: cp " + P + ".baklivetab " + P)
