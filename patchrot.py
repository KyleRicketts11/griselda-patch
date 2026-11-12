#!/usr/bin/env python3
# patchrot.py v2 - model rotation for griselda: when one Google model's daily
# bucket runs dry, she hops to the next model on the same key instead of
# stalling. v1 spliced its block at the end-of-file anchor and broke that
# block's indentation; v2 inserts before the top-level def run_loop line
# instead, which is always safe. Reads an optional models.txt (one model per
# line, first line preferred); models that answer 404 are skipped for the run.
import os, re, shutil, py_compile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(BASE_DIR, "agent.py")
BACKUP = TARGET + ".bakrot"
NL = chr(10)

ROT_CODE = NL.join([
    "# --- model rotation (added by patchrot.py) ---",
    "ROTATION = []",
    "try:",
    "    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), \"models.txt\"), \"r\", encoding=\"utf-8\") as _mf:",
    "        ROTATION = [ln.strip() for ln in _mf if ln.strip()]",
    "except Exception:",
    "    ROTATION = []",
    "if \"MODEL\" in globals() and MODEL and MODEL not in ROTATION:",
    "    ROTATION.insert(0, MODEL)",
    "if not ROTATION:",
    "    ROTATION = [\"gemini-3.5-flash\", \"gemini-3.8-flash\", \"gemini-3.6-flash\", \"gemini-3.5-flash-lite\"]",
    "_DEAD_404 = set()",
    "",
    "def call_gemini_rot(api_key, contents):",
    "    global MODEL",
    "    start = ROTATION.index(MODEL) if MODEL in ROTATION else 0",
    "    order = ROTATION[start:] + ROTATION[:start]",
    "    last_err = None",
    "    for m in order:",
    "        if m in _DEAD_404:",
    "            continue",
    "        MODEL = m",
    "        try:",
    "            return call_gemini(api_key, contents)",
    "        except Exception as e:",
    "            if \"404\" in str(e):",
    "                _DEAD_404.add(m)",
    "                continue",
    "            if \"429\" in str(e):",
    "                last_err = e",
    "                continue",
    "            raise",
    "    if last_err is not None:",
    "        raise last_err",
    "    raise RuntimeError(\"no usable model in rotation\")",
    "# --- end model rotation ---",
])


def main():
    if not os.path.exists(TARGET):
        print("ABORT: agent.py not found")
        return 1
    src = open(TARGET, "r").read()
    if "call_gemini_rot" in src:
        print("ABORT: rotation already installed, nothing changed")
        return 1
    if len(re.findall(r"^def call_gemini\(", src, re.M)) != 1:
        print("ABORT: expected exactly one def call_gemini, found %d" % len(re.findall(r"^def call_gemini\(", src, re.M)))
        return 1
    anchor_pat = re.compile(r"^def run_loop\(", re.M)
    if len(anchor_pat.findall(src)) != 1:
        print("ABORT: expected exactly one top-level def run_loop line, found %d" % len(anchor_pat.findall(src)))
        return 1
    site_pat = re.compile(r"(?<!def )call_gemini\(")
    hits = site_pat.findall(src)
    if len(hits) < 1:
        print("ABORT: no call sites of call_gemini found")
        return 1
    if not re.search(r"^MODEL[ \t]*=", src, re.M):
        print("note: no top-level MODEL constant found, rotation will use its default list")
    shutil.copy2(TARGET, BACKUP)
    print("backup: " + os.path.basename(BACKUP))
    src2 = site_pat.sub("call_gemini_rot(", src)
    src2 = anchor_pat.sub(lambda m: ROT_CODE + NL + NL + m.group(0), src2, count=1)
    open(TARGET, "w").write(src2)
    try:
        py_compile.compile(TARGET, doraise=True)
    except Exception as e:
        shutil.copy2(BACKUP, TARGET)
        print("ABORT: compile failed, backup restored: " + str(e)[:300])
        return 1
    print("compile OK")
    print("agent.py: %d -> %d lines" % (len(src.splitlines()), len(src2.splitlines())))
    print("rewired %d call sites to the rotation wrapper" % len(hits))
    print("next: list her models one per line in models.txt, first line is her preferred model")
    print("when a model's daily bucket runs dry she hops to the next instead of stalling")
    print("restart run_unified.py to load it")
    return 0


raise SystemExit(main())
