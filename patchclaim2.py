#!/usr/bin/env python3
# patchclaim2.py - claim ledger v1 for griselda-brain, anchored to the real agent.py shape
# verified from Kyle's greps on 2026-11-25: menu entry ~142 (col-0 dicts), Groq scout
# prompt ~194, def _save_claim(args) ~459, run_tool dispatch ~551, autonomy allowlist ~603
import ast, os, shutil, sys

def default_src():
    return os.path.join(os.path.expanduser("~"), "griselda-brain", "agent.py")

NEW_BODY = [
    "def norm_claim(t):",
    '    s = " ".join(str(t).lower().split())',
    '    return s.rstrip(" .!?,;")',
    "",
    "def _save_claim(args):",
    '    import json as _json, os as _os',
    '    from datetime import datetime as _dt',
    '    ledger = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "claims.json")',
    "    try:",
    '        with open(ledger, "r", encoding="utf-8") as f:',
    "            data = _json.load(f)",
    "        if not isinstance(data, list):",
    "            data = []",
    "    except Exception:",
    "        data = []",
    '    claim = " ".join(str(args.get("claim", "")).split())',
    "    if not claim:",
    '        return {"error": "claim is required"}',
    "    key = norm_claim(claim)",
    "    for c in data:",
    '        if norm_claim(c.get("claim", "")) == key:',
    '            return {"status": "duplicate", "note": "already in ledger, not saved again", "existing_id": c.get("id")}',
    "    next_num = 1 + max([c.get(\"num\", 0) for c in data] or [0])",
    "    entry = {",
    '        "num": next_num,',
    '        "id": "c-" + str(next_num).zfill(4),',
    '        "claim": claim,',
    '        "source": str(args.get("source", "unknown")),',
    '        "revealed": str(args.get("revealed", "unknown")),',
    '        "status": "active",',
    '        "created": _dt.now().strftime("%Y-%m-%d %H:%M"),',
    "    }",
    "    data.append(entry)",
    '    with open(ledger, "w", encoding="utf-8") as f:',
    "        _json.dump(data, f, ensure_ascii=False, indent=2)",
    '    return {"status": "saved", "id": entry["id"], "total_claims": len(data)}',
    "",
    "def _lookup_claim(args):",
    '    import json as _json, os as _os',
    '    ledger = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "claims.json")',
    "    try:",
    '        with open(ledger, "r", encoding="utf-8") as f:',
    "            data = _json.load(f)",
    "        if not isinstance(data, list):",
    "            data = []",
    "    except Exception:",
    "        data = []",
    '    query = " ".join(str(args.get("query", "") or args.get("claim_id", "") or "").split())',
    "    if not query:",
    '        return {"total": len(data), "claims": data[-10:]}',
    "    q = norm_claim(query)",
    "    hits = []",
    "    for c in data:",
    '        cid = str(c.get("id", "")).lower()',
    '        text = norm_claim(c.get("claim", ""))',
    "        if q == cid or q in text or text in q:",
    "            hits.append(c)",
    '    return {"query": query, "matches": len(hits), "claims": hits[:10]}',
    "",
]

MENU_BLOCK = [
    "{",
    '    "name": "lookup_claim",',
    '    "description": (',
    '        "Search your claim ledger. query: words to match, or a claim id like c-0001. "',
    '        "Returns matching claims with id, claim, source, status, and date."',
    "    ),",
    '    "parameters": {',
    '        "type": "object",',
    '        "properties": {"query": {"type": "string"}},',
    '        "required": [],',
    "    },",
    "},",
]

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else default_src()
    with open(src, "r", encoding="utf-8") as f:
        lines = f.read().split(chr(10))
    stripped = [ln.strip() for ln in lines]
    text = chr(10).join(lines)

    if any(s == "def _lookup_claim(args):" for s in stripped):
        print("PATCH-SKIP: lookup_claim already present, nothing to do")
        return 0

    name_hits = [i for i, s in enumerate(stripped) if s == '"name": "save_claim",']
    disp_hits = [i for i, s in enumerate(stripped) if s == 'if name == "save_claim":']
    def_hits = [i for i, s in enumerate(stripped) if s == "def _save_claim(args):"]
    prompt_key = "'revealed': story point or unknown"
    prompt_hits = text.count(prompt_key)
    allow_key = '("read_url", "save_claim", "write_note"'
    allow_hits = text.count(allow_key)

    if len(name_hits) != 1:
        print("PATCH-FAIL: expected exactly one save_claim menu entry, found " + str(len(name_hits)))
        return 1
    if len(disp_hits) != 1:
        print("PATCH-FAIL: expected exactly one save_claim dispatch line, found " + str(len(disp_hits)))
        return 1
    if len(def_hits) != 1:
        print("PATCH-FAIL: expected exactly one def _save_claim line, found " + str(len(def_hits)))
        return 1
    if prompt_hits != 1:
        print("PATCH-FAIL: expected exactly one prompt mention of save_claim, found " + str(prompt_hits))
        return 1
    if allow_hits != 1:
        print("PATCH-FAIL: expected exactly one autonomy allowlist line, found " + str(allow_hits))
        return 1

    i_name = name_hits[0]
    if stripped[i_name - 1] != "{":
        print("PATCH-FAIL: save_claim menu entry does not start with a bare { line")
        return 1
    j_close = None
    for j in range(i_name, len(lines)):
        if lines[j] == "},":
            j_close = j
            break
    if j_close is None:
        print("PATCH-FAIL: could not find the end of the save_claim menu entry")
        return 1

    i_d = disp_hits[0]
    if stripped[i_d + 1] != "return _save_claim(arguments)":
        print("PATCH-FAIL: dispatch does not return _save_claim(arguments) on the next line")
        return 1
    indent = lines[i_d][: len(lines[i_d]) - len(lines[i_d].lstrip())]
    dispatch_block = [indent + 'if name == "lookup_claim":', indent + "    return _lookup_claim(arguments)"]

    i_f = def_hits[0]
    k_end = None
    for k in range(i_f + 1, len(lines)):
        if lines[k].strip() and lines[k][0] not in (" ", chr(9)):
            k_end = k
            break
    if k_end is None:
        print("PATCH-FAIL: could not find the end of the _save_claim function")
        return 1
    if not (j_close < i_f and k_end <= i_d):
        print("PATCH-FAIL: unexpected line order (menu, def, dispatch)")
        return 1

    new_lines = list(lines)
    new_lines[i_d + 2:i_d + 2] = dispatch_block
    new_lines[i_f:k_end] = NEW_BODY
    new_lines[j_close + 1:j_close + 1] = MENU_BLOCK

    new_text = chr(10).join(new_lines)
    new_text = new_text.replace(
        prompt_key,
        "'revealed': story point or unknown. To check your ledger, use one JSON line of the same style: "
        "{'action': 'lookup_claim', 'query': words to match",
    )
    new_text = new_text.replace(
        allow_key,
        '("read_url", "save_claim", "lookup_claim", "write_note"',
    )

    try:
        ast.parse(new_text)
    except SyntaxError as e:
        print("PATCH-FAIL: patched file would not parse, nothing written (" + str(e) + ")")
        return 1

    bak = src + ".bakclaim"
    shutil.copy2(src, bak)
    with open(src, "w", encoding="utf-8") as f:
        f.write(new_text)
    try:
        ast.parse(open(src, encoding="utf-8").read())
    except SyntaxError:
        shutil.copy2(bak, src)
        print("PATCH-FAIL: write-back failed parse, restored from " + bak)
        return 1

    print("PATCH-OK: claim ledger v1 live")
    print("  backup: " + os.path.basename(bak))
    print("  save_claim: ids, status, duplicate blocking, writes claims.json")
    print("  lookup_claim: added to tool menu, scout prompt, dispatch and autonomy allowlist")
    return 0

if __name__ == "__main__":
    sys.exit(main())
