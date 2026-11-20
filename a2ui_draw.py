#!/usr/bin/env python3
"""griselda's paintbrush: write A2UI wire messages the a2ui page renders live.

usage: python draw.py <verb> [args...]
verbs:
  text words...            add a line of text (quotes optional, words join)
  header words...          add a heading line
  card <title> <body...>   add a card with a title and body
  button words...          add a tappable button (fires event button_pressed)
  clear                    wipe the screen (history stays on file)
  reset                    wipe screen AND history file
every draw goes through the gate as one plain command.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "messages.log")
STATE = os.path.join(HERE, "a2ui_state.json")
CATALOG = "https://a2ui.org/specification/v1_0/catalogs/basic/catalog.json"

def load_state():
    try:
        with open(STATE) as f:
            return json.load(f)
    except Exception:
        return {"n": 0, "children": [], "created": False}

def save_state(s):
    tmp = STATE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(s, f)
    os.replace(tmp, STATE)

def emit(msg):
    with open(LOG, "a") as f:
        f.write(json.dumps(msg) + chr(10))

def push(state, new_components):
    if not state.get("created"):
        emit({"version": "1.0", "createSurface": {"surfaceId": "main", "catalogId": CATALOG}})
        state["created"] = True
    comps = [{"id": "root", "component": "Column", "children": list(state["children"])}] + new_components
    emit({"version": "1.0", "updateComponents": {"surfaceId": "main", "components": comps}})

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__.strip())
        return
    verb = args[0].lower()
    state = load_state()
    if verb == "clear":
        if state.get("created"):
            emit({"version": "1.0", "deleteSurface": {"surfaceId": "main"}})
        state = {"n": 0, "children": [], "created": False}
        save_state(state)
        print("cleared")
        return
    if verb == "reset":
        if state.get("created"):
            emit({"version": "1.0", "deleteSurface": {"surfaceId": "main"}})
        for p in (STATE, LOG):
            try:
                os.remove(p)
            except OSError:
                pass
        print("reset")
        return
    if verb == "text" and len(args) >= 2:
        text = " ".join(args[1:])
        state["n"] += 1
        cid = "t%d" % state["n"]
        state["children"].append(cid)
        push(state, [{"id": cid, "component": "Text", "text": text}])
    elif verb == "header" and len(args) >= 2:
        text = " ".join(args[1:])
        state["n"] += 1
        cid = "h%d" % state["n"]
        state["children"].append(cid)
        push(state, [{"id": cid, "component": "Text", "text": text}])
    elif verb == "card" and len(args) >= 3:
        state["n"] += 1
        base = "c%d" % state["n"]
        state["children"].append(base)
        push(state, [
            {"id": base, "component": "Card", "child": base + "col"},
            {"id": base + "col", "component": "Column", "children": [base + "t", base + "b"]},
            {"id": base + "t", "component": "Text", "text": args[1]},
            {"id": base + "b", "component": "Text", "text": " ".join(args[2:])},
        ])
    elif verb == "button" and len(args) >= 2:
        state["n"] += 1
        base = "b%d" % state["n"]
        state["children"].append(base)
        push(state, [
            {"id": base, "component": "Button", "child": base + "l",
             "action": {"event": {"name": "button_pressed"}}},
            {"id": base + "l", "component": "Text", "text": " ".join(args[1:])},
        ])
    else:
        print("unknown verb or missing args. verbs: text header card button clear reset")
        return
    save_state(state)
    print("drew %s (stroke %d on file)" % (verb, state["n"]))

if __name__ == "__main__":
    main()
