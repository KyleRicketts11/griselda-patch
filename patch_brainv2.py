#!/usr/bin/env python3
# patch_brainv2.py - upgrades her brain page: Kyle's chat asks become real
# tasks she acts on (read a page, run a command, screenshot), her own UI
# redesigns stick, and the page loads its css from the phone. Backs up first.
import os, re, shutil, sys, urllib.request

ROOT = os.path.expanduser("~/griselda-brain")
P = os.path.join(ROOT, "brain.html")
SRC_URL = "https://raw.githubusercontent.com/KyleRicketts11/griselda-patch/main/brain.html"

NEW_SEND = """async function send(){
const box=document.getElementById("say");
const msg=box.value.trim();
if(!msg)return;
box.value="";
S.chat.push({who:"kyle",text:msg});save();render();
ensure_rule();
S.tasks.push({id:"kyle-"+Date.now(),action:"task",task:msg.slice(0,300),status:"pending",origin:"kyle"});
save();render();
log("kyle asked: "+msg.slice(0,60));
setTimeout(function(){cycle();},1500);
}
function ensure_rule(){
const line="you may redesign your own brain page: edit ~/griselda-brain/brain.html and the brain_v3 css files yourself, kyle sees it on refresh";
if(S.rules.join(" ").indexOf("redesign your own brain page")<0){S.rules.push(line);save();}
}
let busy=false;"""

TASK_BRANCH = """if(t.action==="task"){
log("on your ask: "+t.task.slice(0,50));
const p=ctx()+NL+"Kyle asked you: "+t.task+NL+'Answer with ONLY JSON, no prose, no markdown: {"action":"read_url","target":"https://example.com","task":"why"} or {"action":"termux","cmd":"ls","task":"why"} or {"action":"camfox","target":"https://example.com","task":"why"}. Pick the ONE real action that answers him. If no real action fits, answer {"action":"words","say":"your answer in under 2 sentences, no roleplay, no asterisks"}.';
const raw=await think(p);
const ai=raw.indexOf("{"),bi=raw.lastIndexOf("}");
let plan=null;
if(ai>=0&&bi>ai){try{plan=JSON.parse(raw.slice(ai,bi+1));}catch(e){plan=null;}}
const act=plan?String(plan.action||"").trim():"words";
let a2="";
if(!plan||act==="words"||act==="none"){
a2=plan&&plan.say?String(plan.say):raw.slice(0,400);
}else if(act==="read_url"){
const target=String(plan.target||"").trim();
if(target.indexOf("http")!==0){a2="I could not form a real action for that yet.";}
else{const page=await readPage(target);a2=await think(ctx()+NL+"Kyle asked: "+t.task+NL+"You read "+target+" and got:"+NL+page+NL+"Answer Kyle directly with what you found, short, no story prose.");S.notes.push(new Date().toISOString()+" kyle-ask read_url "+target);}
}else if(act==="termux"){
const cmd=String(plan.cmd||"").slice(0,500);
if(!cmd){a2="I could not form a real action for that yet.";}
else{const out=await bridgeCmd(cmd);a2=await think(ctx()+NL+"Kyle asked: "+t.task+NL+"You ran on the phone: "+cmd+NL+"The gate returned:"+NL+out.slice(0,6000)+NL+"Answer Kyle directly, short, no story prose.");S.notes.push(new Date().toISOString()+" kyle-ask termux "+cmd.slice(0,60));}
}else if(act==="camfox"){
const target=String(plan.target||"").trim();
if(target.indexOf("http")!==0){a2="I could not form a real action for that yet.";}
else{const shot=await bridgeShot(target);a2=await think(ctx()+NL+"Kyle asked: "+t.task+NL+"You took a real screenshot of "+target+" with your own browser. Look at it and answer Kyle directly, short, no story prose.",shot);S.notes.push(new Date().toISOString()+" kyle-ask camfox "+target);}
}else{
a2="I could not turn that into an action yet.";
}
t.status="done";t.answer=a2.slice(0,800);save();
S.chat.push({who:"griselda",text:"[acted] "+a2.slice(0,500)});
log("kyle ask done","grn");save();
return;
}
"""

def main():
    if os.path.exists(P):
        shutil.copy2(P, P + ".bakv1")
    req = urllib.request.Request(SRC_URL, headers={"User-Agent": "griselda-patch"})
    src = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    src = src.replace("https://raw.githack.com/KyleRicketts11/griselda-patch/main/", "")
    src = src.replace("https://cdn.jsdelivr.net/gh/KyleRicketts11/griselda-patch@main/", "")
    assert 'href="brain_v3.css"' in src, "css rewrite failed"
    m = re.search(r"async function send\(\)\{.*?\n\}\nlet busy=false;", src, re.S)
    assert m, "send anchor missing"
    src = src[:m.start()] + NEW_SEND + src[m.end():]
    anchor = 'log("working: "+t.action+" "+(t.target||t.cmd));' + chr(10)
    assert anchor in src, "working anchor missing"
    src = src.replace(anchor, anchor + TASK_BRANCH, 1)
    old_end = '}catch(e){log("cycle failed: "+e.message,"red");}' + chr(10) + 'busy=false;render();' + chr(10) + '}'
    assert old_end in src, "cycle end anchor missing"
    src = src.replace(old_end, '}catch(e){log("cycle failed: "+e.message,"red");}finally{busy=false;render();}' + chr(10) + '}', 1)
    js = src.split("<script>")[1].split("</script>")[0]
    assert js.count("{") == js.count("}"), "braces unbalanced"
    assert js.count("(") == js.count(")"), "parens unbalanced"
    with open(P, "w") as f:
        f.write(src)
    print("brain.html upgraded: your asks become her actions, redesigns stick")
    print("checks passed, backup: brain.html.bakv1")
    return 0

sys.exit(main())
