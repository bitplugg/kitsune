"""api/serve — REST API поверх общей базы (stdlib): /api/hosts, /api/loot, ..."""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from kitsune import db
from kitsune.framework import Module


def _rows(sql):
    return [dict(r) for r in db.query(sql)]


class Handler(BaseHTTPRequestHandler):
    ROUTES = {
        "/api/hosts":    lambda: _rows("SELECT * FROM hosts ORDER BY id"),
        "/api/ports":    lambda: _rows(
            "SELECT h.host, p.port, p.proto, p.service, p.banner FROM ports p "
            "JOIN hosts h ON h.id=p.host_id ORDER BY h.host, p.port"),
        "/api/subdomains": lambda: _rows("SELECT * FROM subdomains ORDER BY name"),
        "/api/loot":     lambda: _rows("SELECT * FROM loot ORDER BY id"),
        "/api/sessions": lambda: _rows("SELECT * FROM sessions ORDER BY id"),
        "/api/stats":    lambda: db.stat(),
        "/api/report":   None,   # отдельно ниже
    }

    def log_message(self, *a):  # тише в цикле REPL
        pass

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/api/report":
            self._send_markdown()
            return
        handler = self.ROUTES.get(path)
        if handler is None:
            self._send(404, {"error": f"unknown endpoint {path}",
                             "available": sorted(list(self.ROUTES) + ["/api/report"])})
            return
        self._send(200, {"endpoint": path, "data": handler()})

    def _send(self, code, payload):
        body = json.dumps(payload, default=str, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_markdown(self):
        from kitsune.report_md import build_markdown
        md = build_markdown()
        body = md.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/markdown; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class Module(Module):
    meta = {
        "name": "api/serve",
        "author": "kitsune",
        "description": "REST API over session DB: /api/hosts /api/loot /api/report /api/stats",
        "options": {
            "port":    {"default": "8000", "required": True, "desc": "listen port"},
            "host":    {"default": "127.0.0.1", "required": False, "desc": "bind address"},
            "seconds": {"default": "60", "required": False, "desc": "uptime"},
        },
    }

    def run(self):
        try:
            server = ThreadingHTTPServer((self.host, int(self.port)), Handler)
        except OSError as e:
            self.fail(f"can't bind {self.host}:{self.port}: {e}")
            return

        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.ok(f"API up on http://{self.host}:{self.port}/api/stats  (uptime {self.seconds}s)")
        self.status("endpoints: /api/hosts /api/ports /api/loot /api/sessions /api/stats /api/report")
        try:
            time.sleep(float(self.seconds))
        except KeyboardInterrupt:
            pass
        server.shutdown()
        thread.join(timeout=3)
        self.status("API stopped")
