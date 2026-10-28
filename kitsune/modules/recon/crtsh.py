"""recon/crtsh — субдомены через Certificate Transparency (crt.sh JSON API)."""

import json
import urllib.request

from kitsune import db
from kitsune.framework import Module


class Module(Module):
    meta = {
        "name": "recon/crtsh",
        "author": "kitsune",
        "description": "Passive subdomain discovery via crt.sh certificate transparency log",
        "options": {
            "domain":  {"default": "", "required": True, "desc": "domain, e.g. example.com"},
            "timeout": {"default": "15", "required": False, "desc": "http timeout"},
        },
    }

    def run(self):
        url = f"https://crt.sh/?q=%25.{self.domain}&output=json"
        self.status(f"querying crt.sh for *.{self.domain} (may take a while) ...")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "kitsune/0.1"})
            with urllib.request.urlopen(req, timeout=float(self.timeout)) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
        except Exception as e:  # noqa: BLE001
            self.fail(f"crt.sh query failed: {e}")
            return

        names = set()
        for row in data:
            for n in str(row.get("name_value", "")).split("\n"):
                n = n.strip().lower().lstrip("*.")
                if n.endswith(f".{self.domain}".lower()) and n != self.domain.lower():
                    names.add(n)

        new = []
        for name in sorted(names):
            if db.add_subdomain(name):
                new.append((name, ""))
        self.ok(f"crt.sh: {len(names)} unique, {len(new)} new -> db")
        if names:
            self.table(("Subdomain",), [(n,) for n in sorted(names)])
