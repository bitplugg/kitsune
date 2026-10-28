"""team/sync — обмен результатами между операторами (push/serve, stdlib HTTP)."""

import json
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from kitsune import db
from kitsune.framework import Module


class Module(Module):
    meta = {
        "name": "team/sync",
        "author": "kitsune",
        "description": "Share loot/hosts with another operator: `mode=serve` host the sync, `mode=push` send",
        "options": {
            "mode":    {"default": "serve", "required": True, "desc": "serve | push"},
            "port":    {"default": "9901", "required": False, "desc": "sync port"},
            "remote":  {"default": "127.0.0.1", "required": False, "desc": "remote host (push mode)"},
            "seconds": {"default": "60", "required": False, "desc": "serve uptime"},
        },
    }

    def run(self):
        mode = self.mode.lower().strip()
        if mode == "serve":
            self._serve()
        elif mode == "push":
            self._push()
        else:
            self.fail("mode must be serve | push")

    # -------------------------------------------------------------- serve
    def _serve(self):
        port = int(self.port)
        try:
            server = ThreadingHTTPServer(("0.0.0.0", port), SyncHandler)
        except OSError as e:
            self.fail(f"can't bind :{port}: {e}")
            return
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        SyncHandler.baseline = db.stat()
        self.ok(f"team sync server on 0.0.0.0:{port} — other operators: "
                f"`use team/sync` / `set mode push` / `set remote <ip>` / run")
        try:
            time.sleep(float(self.seconds))
        except KeyboardInterrupt:
            pass
        server.shutdown()
        thread.join(timeout=3)
        after = db.stat()
        delta = {k: after[k] - SyncHandler.baseline.get(k, 0) for k in after}
        self.ok(f"sync finished, received: {delta}")

    # --------------------------------------------------------------- push
    def _push(self):
        payload = {
            "hosts": [dict(r) for r in db.query("SELECT host, hostname FROM hosts")],
            "ports": [dict(r) for r in db.query(
                "SELECT h.host, p.port, p.service FROM ports p "
                "JOIN hosts h ON h.id=p.host_id")],
            "loot": [dict(r) for r in db.query(
                "SELECT category, target, data FROM loot")],
        }
        url = f"http://{self.remote}:{int(self.port)}/merge"
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.status(f"pushing {len(payload['hosts'])} hosts / "
                    f"{len(payload['ports'])} ports / {len(payload['loot'])} loot -> {url}")
        try:
            req = urllib.request.Request(url, data=body,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode())
        except OSError as e:
            self.fail(f"push failed: {e}")
            return
        self.ok(f"remote accepted: {result}")


class SyncHandler(BaseHTTPRequestHandler):
    """Серверная часть: POST /merge — вливаем чужие результаты."""
    baseline = {}

    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path == "/api/stats":
            self._json(200, db.stat())
        else:
            self._json(404, {"error": "try POST /merge"})

    def do_POST(self):
        if self.path != "/merge":
            self._json(404, {"error": "unknown"})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length).decode())
        except (ValueError, OSError) as e:
            self._json(400, {"error": str(e)})
            return

        for row in data.get("hosts", []):
            db.execute("INSERT OR IGNORE INTO hosts (host, hostname, source) "
                       "VALUES (?,?,'team_sync')", (row.get("host"), row.get("hostname")))
        for row in data.get("ports", []):
            db.add_port(row.get("host", ""), int(row.get("port", 0)), service=row.get("service", ""))
        for row in data.get("loot", []):
            db.add_loot(row.get("category", "team"), row.get("target", ""), row.get("data", ""))

        after = db.stat()
        delta = {k: after[k] - before.get(k, 0) for k in after}
        self._json(200, {"merged": delta})

    def _json(self, code, payload):
        body = json.dumps(payload, default=str, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
