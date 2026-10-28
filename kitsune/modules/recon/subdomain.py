"""recon/subdomain — DNS-брутфорс субдоменов (аналог dnsrecon из wordlist'а)."""

import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

from kitsune import db
from kitsune.framework import Module

WORDS = [
    "www", "mail", "ftp", "ns1", "ns2", "vpn", "dev", "staging", "stage",
    "test", "qa", "uat", "demo", "beta", "alpha", "admin", "portal",
    "intranet", "git", "gitlab", "jenkins", "ci", "api", "app", "web", "webmail",
    "mx", "smtp", "pop", "imap", "cdn", "static", "media", "assets", "img",
    "shop", "store", "blog", "news", "forum", "wiki", "docs", "help",
    "support", "support-old", "cpanel", "whm", "db", "mysql", "postgres",
    "redis", "mongo", "elastic", "kibana", "grafana", "prometheus", "status",
    "monitor", "monitoring", "zabbix", "backup", "backup-old", "old", "new",
]  # ~65


class Module(Module):
    meta = {
        "name": "recon/subdomain",
        "author": "kitsune",
        "description": "Bruteforce subdomains via DNS over embedded wordlist",
        "options": {
            "domain":  {"default": "", "required": True, "desc": "base domain, e.g. example.com"},
            "threads": {"default": "50", "required": False, "desc": "concurrency"},
            "wordlist": {"default": "", "required": False, "desc": "path to custom wordlist, one word per line"},
        },
    }

    def run(self):
        words = WORDS
        if self.wordlist:
            try:
                with open(self.wordlist, encoding="utf-8") as f:
                    extra = [w.strip().lower() for w in f if w.strip()]
                if extra:
                    words = extra
            except OSError as e:
                self.fail(f"can't read wordlist: {e}")
                return
        candidates = {f"{w}.{self.domain}" for w in words}
        self.status(f"resolving {len(candidates)} candidates ({self.domain})")

        socket.setdefaulttimeout(3.0)
        found = []
        with ThreadPoolExecutor(max_workers=int(self.threads)) as pool:
            futures = {pool.submit(self._resolve, c): c for c in candidates}
            for fut in as_completed(futures):
                result = fut.result()
                if result:
                    found.append(result)

        new = []
        for name, ip in sorted(found):
            if db.add_subdomain(name, ip):
                db.upsert_host(ip, hostname=name, source="subdomain")
                new.append((name, ip))

        self.ok(f"{len(found)} alive, {len(new)} new in db")
        if found:
            self.table(("Subdomain", "IP"), [(n, i) for n, i in sorted(found)])

    @staticmethod
    def _resolve(name: str):
        try:
            return (name, socket.gethostbyname(name))
        except socket.error:
            return None
