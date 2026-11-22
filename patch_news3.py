import shutil
src = open("agent.py", encoding="utf-8").read()
NL = chr(10)
URL = "https://raw.githubusercontent.com/KyleRicketts11/griselda-patch/main/scout_steals.txt"
LINE = 'SCOUT = "' + URL + '"'
if "SCOUT = " in src:
    print("ALREADY-OK")
elif "def news_grab_check():" not in src:
    print("news block missing, nothing to patch")
else:
    shutil.copy("agent.py", "agent.py.baknews3")
    src = src.replace("def news_grab_check():", LINE + NL + NL + "def news_grab_check():", 1)
    open("agent.py", "w", encoding="utf-8").write(src)
    import py_compile
    py_compile.compile("agent.py", doraise=True)
    print("FIX-OK")
