"""recon/whois — классический whois через порт 43 (raw socket, stdlib)."""

import socket

from kitsune import db
from kitsune.framework import Module

WHOIS_SERVERS = {
    "com": "whois.verisign-grs.com",
    "net": "whois.verisign-grs.com",
    "org": "whois.pir.org",
    "ru":  "whois.tcinet.ru",
    "io":  "whois.nic.io",
    "dev": "whois.nic.google",
    "info": "whois.afilias.net",
}


class Module(Module):
    meta = {
        "name": "recon/whois",
        "author": "kitsune",
        "description": "Simple whois lookup over port 43",
        "options": {
            "domain": {"default": "", "required": True, "desc": "domain, e.g. example.com"},
            "timeout": {"default": "10", "required": False, "desc": "socket timeout"},
        },
    }

    def run(self):
        name = self.domain.strip().lower().split("/")[-1]
        if "." not in name:
            self.fail("need domain like example.com")
            return
        tld = name.rsplit(".", 1)[-1]
        server = WHOIS_SERVERS.get(tld)
        if not server:
            self.fail(f"no built-in whois server for .{tld} (patch WHOIS_SERVERS)")
            return

        self.status(f"whois {name} via {server}:43")
        try:
            with socket.create_connection((server, 43), timeout=float(self.timeout)) as s:
                s.sendall(f"{name}\r\n".encode())
                chunks = []
                while True:
                    data = s.recv(4096)
                    if not data:
                        break
                    chunks.append(data.decode("utf-8", errors="replace"))
        except OSError as e:
            self.fail(f"whois query failed: {e}")
            return

        text = "\n".join(chunks)
        key_lines = [l.strip() for l in text.splitlines()
                     if any(k in l.lower() for k in
                            ("registrant", "creation date", "expiry", "registrar:",
                             "name server", "registrar whois", "domain name"))][:12]
        db.add_loot("whois", name, "; ".join(key_lines))
        self.ok("saved to loot")
        for l in key_lines:
            self.print(l)
