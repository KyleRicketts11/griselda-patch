import os
home = os.path.expanduser('~')
p = os.path.join(home, 'griselda-brain', 'agent.py')
src = open(p).read()
lines = src.split(chr(10))
hits = [i for i, l in enumerate(lines) if 'not readable' in l]
if not hits:
    print('no hits for not readable')
else:
    print('found at lines:', ', '.join(str(i + 1) for i in hits))
    lo = max(0, hits[0] - 45)
    hi = min(len(lines), hits[-1] + 12)
    for n in range(lo, hi):
        print(str(n + 1) + ': ' + lines[n])
