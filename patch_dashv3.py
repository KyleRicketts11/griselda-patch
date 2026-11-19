#!/usr/bin/env python3
import re, os, shutil, sys

p = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/griselda-brain/brain.html")
src = open(p, encoding="utf-8").read()
d = os.path.dirname(os.path.abspath(p))
backup = os.path.join(d, "brain.html.bakdash")
if not os.path.exists(backup):
    shutil.copy2(p, backup)
    print("backup:", backup)

NEW = '''<section id="v-dash" style="display:none">
<div class="card"><span class="tag">LIVE</span> <b>her brain, live from port 5000</b> <small id="dashstamp"></small><small id="dashdate" style="display:none"></small></div>
<div class="card"><pre id="dashlive">waiting for her state...</pre></div>
<div class="row"><button onclick="refreshDash()">refresh now</button></div>
<div class="card log">this tab is part of her own page now: the numbers come straight from her brain on port 5000 through the gate, and the page itself is brain.html, hers to redesign whenever she wants.</div>
</section>'''

JS = '''let dashTimer=null;
async function refreshDash(){
try{
const hs=await fetch(S.bridge+"/dash/her_state");
const t=await hs.text();
let pretty=t.trim();
try{const j=JSON.parse(t);pretty=Object.keys(j).map(function(k){const v=j[k];const s=(typeof v==="object")?JSON.stringify(v):String(v);return k+": "+s;}).join(NL+NL);}catch(e){}
document.getElementById("dashlive").textContent=pretty.slice(0,8000)||"(empty state)";
document.getElementById("dashstamp").textContent="updated "+new Date().toLocaleTimeString();
try{
const lv=await fetch(S.bridge+"/dash/live");
const lt=(await lv.text()).trim();
if(lt){document.getElementById("dashlive").textContent+=NL+NL+"live: "+lt.slice(0,400);}
}catch(e){}
}catch(e){
document.getElementById("dashlive").textContent="her brain is not answering. is run_unified still running on port 5000?"+NL+e.message;
document.getElementById("dashstamp").textContent="";
}
}
function dashWatch(){
const on=(document.getElementById("v-dash").style.display!=="none")&&(document.visibilityState==="visible");
if(on&&!dashTimer){refreshDash();dashTimer=setInterval(refreshDash,10000);}
if(!on&&dashTimer){clearInterval(dashTimer);dashTimer=null;}
}
setInterval(dashWatch,2000);

'''

pat = re.compile(r'<section id="v-dash".*?</section>', re.S)
if not pat.search(src):
    print("FAIL: could not find the dashboard section")
    sys.exit(1)
src = pat.sub(lambda m: NEW, src, count=1)
anchor = "function render()"
if anchor not in src:
    print("FAIL: could not find the render anchor")
    sys.exit(1)
src = src.replace(anchor, JS + anchor, 1)
open(p, "w", encoding="utf-8").write(src)
nsec = len(pat.findall(src))
brd = src.count("{") - src.count("}")
prd = src.count("(") - src.count(")")
print("patched:", p)
print("v-dash sections =", nsec, "| refreshDash refs =", src.count("refreshDash"), "| dashWatch refs =", src.count("dashWatch"))
print("brace delta =", brd, "| paren delta =", prd, "| size =", len(src))
print("PATCH-OK" if (nsec == 1 and src.count("refreshDash") >= 3 and src.count("dashWatch") >= 2 and brd == 0 and prd == 0) else "PATCH-CHECKS-FAILED")
