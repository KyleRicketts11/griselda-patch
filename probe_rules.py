#!/usr/bin/env python3
# probe_rules.py - shows how griselda's prompt and rules are defined in agent.py
# read-only, changes nothing
import re

src = open("agent.py", encoding="utf-8").read()
lines = src.split(chr(10))
pats = re.compile(r"SYSTEM|system_|GRISELDA|RULES|rules|persona|soul|You are|never|locked", re.IGNORECASE)
hits = 0
for i, ln in enumerate(lines, 1):
    if pats.search(ln):
        hits += 1
        if hits <= 90:
            print(str(i) + ": " + ln[:180])
print("total matches: " + str(hits))
