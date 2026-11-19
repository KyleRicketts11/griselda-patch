#!/usr/bin/env python3
# make_image.py - griselda's image tool: prompt -> picture saved to Kyle's gallery.
# usage: python make_image.py "a friendly green-faced witch portrait"
# free, no api key needed (pollinations). saves to ~/storage/pictures when
# termux-setup-storage has been run, else to ~/griselda-brain.
import sys, os, time, urllib.request, urllib.parse

prompt = " ".join(sys.argv[1:]).strip()
if not prompt:
    prompt = "a friendly green-faced witch named griselda, warm portrait, digital art"

url = ("https://image.pollinations.ai/prompt/"
       + urllib.parse.quote(prompt)
       + "?width=768&height=768&nologo=true&seed=" + str(int(time.time()) % 100000))

req = urllib.request.Request(url, headers={"User-Agent": "griselda-brain/1.0"})
try:
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
except Exception as e:
    raise SystemExit("IMAGE-FAIL fetch: %s" % e)

if len(data) < 2000 or not (data[:3] == b"\xff\xd8\xff" or data[:8] == b"\x89PNG\r\n\x1a\n"):
    raise SystemExit("IMAGE-FAIL bad bytes (%d)" % len(data))

outdir = os.path.expanduser("~/storage/pictures")
if not os.path.isdir(outdir):
    outdir = os.path.expanduser("~/griselda-brain")
path = os.path.join(outdir, "griselda_%d.jpg" % int(time.time()))
with open(path, "wb") as f:
    f.write(data)
print("IMAGE-OK %s (%d bytes)" % (path, len(data)))
