import json, os, base64, subprocess, urllib.request, re
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = os.path.expanduser("~/griselda-brain")
PORT = 5001
BRAIN_URL = "https://raw.githubusercontent.com/KyleRicketts11/griselda-patch/main/brain.html"
CSS_FILES = ["brain_v3.css","brain_v3_bg.css","brain_v3_bg2.css","brain_v3_anim.css","brain_v3_move.css","brain_v3_bg3.css"]
CDN_BASE = "https://cdn.jsdelivr.net/gh/KyleRicketts11/griselda-patch@main/"
CT = {".html":"text/html; charset=utf-8",".css":"text/css; charset=utf-8",".js":"application/javascript",".png":"image/png",".jpg":"image/jpeg",".jpeg":"image/jpeg",".svg":"image/svg+xml",".json":"application/json",".txt":"text/plain; charset=utf-8"}

def fetch(url, dest):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "griselda-gate"})
        data = urllib.request.urlopen(req, timeout=20).read()
        tmp = dest + ".tmp"
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, dest)
        return True
    except Exception:
        return False

def ensure_assets():
    p = os.path.join(ROOT, "brain.html")
    if not os.path.exists(p):
        fetch(BRAIN_URL, p)
    for c in CSS_FILES:
        cp = os.path.join(ROOT, c)
        if not os.path.exists(cp):
            fetch(CDN_BASE + c, cp)

class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/dash" or path.startswith("/dash/"):
            target = "http://127.0.0.1:5000" + self.path[5:]
            try:
                req = urllib.request.Request(target, headers={"User-Agent": "griselda-gate"})
                r = urllib.request.urlopen(req, timeout=15)
                data = r.read()
                ct = r.headers.get("Content-Type") or "application/json"
                r.close()
                self._send(200, data, ct)
            except Exception as e:
                self._send(200, json.dumps({"offline": str(e)}).encode())
            return
        if path in ("/", "/brain.html", "/index.html", "/brain"):
            ensure_assets()
            p = os.path.join(ROOT, "brain.html")
            if os.path.exists(p):
                with open(p, "rb") as f:
                    self._send(200, f.read(), "text/html; charset=utf-8")
            else:
                self._send(500, json.dumps({"error": "brain.html missing and download failed"}).encode())
            return
        if path == "/ping":
            self._send(200, b'{"ok":true}')
            return
        m = re.match(r"^/([A-Za-z0-9_.\-]+)$", path)
        if m:
            name = m.group(1)
            if not name.startswith("."):
                p = os.path.join(ROOT, name)
                if os.path.isfile(p):
                    ext = os.path.splitext(name)[1].lower()
                    with open(p, "rb") as f:
                        self._send(200, f.read(), CT.get(ext, "application/octet-stream"))
                    return
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

print("griselda gate bridge v3 on http://127.0.0.1:5001 (brain page + her files + her dashboard live)")
HTTPServer(("127.0.0.1", PORT), H).serve_forever()
