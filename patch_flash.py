import shutil
p="/data/data/com.termux/files/home/griselda-brain/agent.py"
src=open(p).read()
old="gemini-2.0-flash"
new="gemini-2.5-flash"
n=src.count(old)
if n==0:
    print("no old model refs found in agent.py, nothing to change")
else:
    shutil.copy(p,p+".bakflash")
    open(p,"w").write(src.replace(old,new))
    print("swapped",n,"refs to gemini-2.5-flash, backup saved as agent.py.bakflash")
