"""network/discovery — discovery живых хостов TCP-connect брютом по /CIDR."""

import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed

from kitsune import db
from kitsune.framework import Module

PROBE_PORTS = [22, 80, 443, 445, 3389, 8080]
MAX_HOSTS = 4096


class Module(Module):
    meta = {
        "name": "network/discovery",
        "author": "kitsune",
        "description": "Host discovery: quick TCP-connect sweep over subnet for common ports",
        "options": {
            "target":  {"default": "", "required": True, "desc": "CIDR, e.g. 192.168.1.0/24"},
            "ports":   {"default": "22,80,443,445,3389,8080", "required": False, "desc": "probe port list"},
            "threads": {"default": "300", "required": False, "desc": "concurrency"},
            "timeout": {"default": "0.8", "required": False, "desc": "connect timeout"},
        },
    }

    def run(self):
        try:
            net = ipaddress.ip_network(self.target.strip(), strict=False)
        except ValueError as e:
            self.fail(f"bad cidr: {e}")
            return
        if net.num_addresses > MAX_HOSTS + 2:
            self.fail(f"network too big (>{MAX_HOSTS} hosts)")
            return

        ports = []
        for chunk in self.ports.split(","):
            chunk = chunk.strip()
            if "-" in chunk:
                a, b = chunk.split("-")
                ports += list(range(int(a), int(b) + 1))
            elif chunk.isdigit():
                ports.append(int(chunk))
        if not ports:
            self.fail("no valid ports")
            return

        hosts = [str(x) for x in net.hosts()]
        self.status(f"sweeping {len(hosts)} hosts x {len(ports)} ports")

        alive = []
        with ThreadPoolExecutor(max_workers=int(self.threads)) as pool:
            futures = {pool.submit(self._probe, h, p, float(self.timeout)): h
                       for h in hosts for p in ports}
            for fut in as_completed(futures):
                if fut.result():
                    host = futures[fut]
                    if host not in alive:
                        alive.append(host)

        for host in alive:
            db.upsert_host(host, source="discovery")
        self.ok(f"{len(alive)} alive host(s) -> db")
        if alive:
            self.table(("Host",), [(h,) for h in sorted(alive)])

    @staticmethod
    def _probe(host, port, timeout):
        import socket
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (ConnectionRefusedError, socket.timeout, OSError):
            return False
