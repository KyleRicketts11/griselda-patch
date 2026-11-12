import os, re

home = os.path.expanduser('~')
p = os.path.join(home, 'griselda-brain', 'agent.py')
src = open(p, encoding='utf-8', errors='replace').read()
lines = src.split(chr(10))
print('agent.py lines:', len(lines))

def show(pattern, label, maxhits=4):
    print('== ' + label)
    hits = 0
    for i, l in enumerate(lines):
        if re.search(pattern, l):
            print(str(i + 1) + ': ' + l.strip()[:160])
            hits += 1
            if hits >= maxhits:
                break
    if hits == 0:
        print('none')

show(r'def tool|TOOLS|tools\s*=', 'tool registry')
show(r'read_url', 'read_url hits', 6)
show(r'functionCall|function_call', 'function call handling', 6)
show(r'brain_notes', 'note saving', 6)
show(r'agent_memory|memory\.json|tasks\.json', 'data files', 6)
show(r'api_key', 'api key line', 3)

dash = os.path.join(home, 'griselda-brain', 'dashboard')
if os.path.isdir(dash):
    print('dashboard dir:', sorted(os.listdir(dash)))
else:
    print('no dashboard dir in griselda-brain')
