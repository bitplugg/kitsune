"""recon/dnsenum — быстрый DNS-перебор: A/AAAA, PTR, канонические имена."""

import socket
from concurrent.futures import ThreadPoolExecutor

from kitsune import db
from kitsune.framework import Module

RECORD_CHECKS = ["A", "AAAA"]


class Module(Module):
    meta = {
        "name": "recon/dnsenum",
        "author": "kitsune",
        "description": "Quick DNS recon: resolve A/AAAA, guess service hosts, reverse PTR",
        "options": {
            "domain": {"default": "", "required": True, "desc": "domain, e.g. example.com"},
            "threads": {"default": "20", "required": False, "desc": "concurrency"},
        },
    }

    GUESS = ["www", "mail", "mx", "ns1", "ns2", "api", "vpn", "remote", "m"]

    def run(self):
        name = self.domain.strip()
        candidates = [name, f"www.{name}"] + [f"{g}.{name}" for g in self.GUESS]

        self.status(f"resolving {len(candidates)} names")
        results = []
        with ThreadPoolExecutor(max_workers=int(self.threads)) as pool:
            for n, addrs in pool.map(self._resolve, candidates):
                if addrs:
                    results.append((n, ", ".join(addrs)))

        ptr = ""
        try:
            ip = socket.gethostbyname(name)
            ptr_host, _, _ = socket.gethostbyaddr(ip)
            if ptr_host and not ptr_host.startswith(name[:4]):
                ptr = ptr_host
        except (socket.error, OSError):
            pass

        if results:
            for n, a in results:
                db.add_subdomain(n, a.split(",")[0])
            self.ok(f"{len(results)} resolved -> db")
            self.table(("Name", "Address"), results)
            if ptr:
                self.table(("PTR",), [(ptr,)])
        else:
            self.fail("no records resolved")

    @staticmethod
    def _resolve(name):
        try:
            info = socket.getaddrinfo(name, None)
            addrs = {i[4][0] for i in info}
            return (name, sorted(addrs))
        except (socket.error, OSError):
            return (name, [])
