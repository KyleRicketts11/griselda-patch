import shutil
p="/data/data/com.termux/files/home/griselda-brain/agent.py"
src=open(p).read()
n=src.count("gemini-2.0-flash")+src.count("gemini-2.5-flash")
if n==0:
    print("no retired model names found, nothing to change")
else:
    shutil.copy(p,p+".bakflash2")
    src=src.replace("gemini-2.0-flash","gemini-flash-latest")
    src=src.replace("gemini-2.5-flash","gemini-flash-latest")
    open(p,"w").write(src)
    print("swapped",n,"retired model refs to gemini-flash-latest, backup saved as agent.py.bakflash2")
