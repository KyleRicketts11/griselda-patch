#!/usr/bin/env python3
import os, shutil, sys

p = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/griselda-brain/brain.html")
src = open(p, encoding="utf-8").read()
d = os.path.dirname(os.path.abspath(p))
backup = os.path.join(d, "brain.html.bakchat")
if not os.path.exists(backup):
    shutil.copy2(p, backup)
    print("backup:", backup)

OLD1 = 'let chain=["gemini-flash-latest"];'
NEW1 = 'let chain=["gemini-flash-lite-latest","gemini-flash-latest"];'
OLD2 = 'if(es.indexOf("404")>=0||es.indexOf("503")>=0||es.indexOf("no longer available")>=0)break;'
NEW2 = 'if(es.indexOf("404")>=0||es.indexOf("503")>=0||es.indexOf("429")>=0||es.indexOf("no longer available")>=0)break;'

if OLD1 not in src:
    print("FAIL: chain line not found (maybe already patched)")
    sys.exit(1)
if OLD2 not in src:
    print("FAIL: retry line not found")
    sys.exit(1)
src = src.replace(OLD1, NEW1, 1)
src = src.replace(OLD2, NEW2, 1)
open(p, "w", encoding="utf-8").write(src)
ok = (NEW1 in src and NEW2 in src and OLD1 not in src and OLD2 not in src and
      src.count("{") - src.count("}") == 0 and src.count("(") - src.count(")") == 0)
print("patched:", p)
print("working model first:", NEW1 in src, "| skips quota models:", NEW2 in src)
print("size:", len(src))
print("PATCH-OK" if ok else "PATCH-CHECKS-FAILED")
