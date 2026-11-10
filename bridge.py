import json, os, base64, subprocess, urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = os.path.expanduser("~/griselda-brain")
PORT = 5001
BRAIN_URL = "https://raw.githubusercontent.com/KyleRicketts11/griselda-patch/main/brain.html"

def get_brain():
    p = os.path.join(ROOT, "brain.html")
    try:
        data = urllib.request.urlopen(BRAIN_URL, timeout=20).read()
        with open(p, "wb") as f:
            f.write(data)
    except Exception:
        if not os.path.exists(p):
            raise
    with open(p, "rb") as f:
        return f.read()

class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def do_GET(self):
        if self.path in ("/", "/brain.html", "/index.html"):
            try:
                self._send(200, get_brain(), "text/html; charset=utf-8")
            except Exception as e:
                self._send(500, json.dumps({"error": str(e)}).encode())
        elif self.path == "/ping":
            self._send(200, b'{"ok":true}')
        else:
            self._send(404, b'{"error":"not found"}')
    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        try:
            req = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            req = {}
        if self.path == "/cmd":
            cmd = str(req.get("cmd") or "")[:2000]
            if not cmd:
                self._send(400, b'{"error":"no cmd"}')
                return
            try:
                r = subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True, timeout=180)
                out = (r.stdout + r.stderr).decode("utf-8", "replace")[-8000:]
                self._send(200, json.dumps({"code": r.returncode, "out": out}).encode())
            except Exception as e:
                self._send(200, json.dumps({"code": -1, "out": "FAILED: " + str(e)}).encode())
        elif self.path == "/camfox":
            url = str(req.get("url") or "")
            if not url.startswith("http"):
                self._send(400, b'{"error":"bad url"}')
                return
            shot = os.path.join(ROOT, "bridge_shot.png")
            try:
                subprocess.run(["camfox", "-headless", "--screenshot", shot, url], cwd=ROOT, capture_output=True, timeout=120)
                if not os.path.exists(shot):
                    self._send(200, json.dumps({"error": "no screenshot produced"}).encode())
                    return
                with open(shot, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                self._send(200, json.dumps({"shot": b64}).encode())
            except Exception as e:
                self._send(200, json.dumps({"error": str(e)}).encode())
        else:
            self._send(404, b'{"error":"not found"}')
    def log_message(self, *a):
        pass

print("griselda gate bridge on http://127.0.0.1:" + str(PORT) + "/brain.html")
HTTPServer(("127.0.0.1", PORT), H).serve_forever()
