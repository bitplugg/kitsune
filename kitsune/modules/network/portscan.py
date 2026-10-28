"""network/portscan — TCP-сканер на чистых сокетах (без nmap)."""

import ipaddress
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

from kitsune import db
from kitsune.framework import Module

TOP_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445, 465, 587,
    993, 995, 1433, 1521, 1723, 2049, 3306, 3389, 5432, 5900, 6379,
    8080, 8443, 8888, 9200, 27017,
]

SERVICES = {
    21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp", 53: "domain", 80: "http",
    110: "pop3", 111: "rpc", 135: "msrpc", 139: "netbios", 143: "imap",
    443: "https", 445: "smb", 465: "smtps", 587: "submission", 993: "imaps",
    995: "pop3s", 1433: "mssql", 1521: "oracle", 3306: "mysql", 3389: "rdp",
    5432: "postgres", 5900: "vnc", 6379: "redis", 8080: "http-proxy",
    8443: "https-alt", 8888: "http-alt", 9200: "elasticsearch", 27017: "mongodb",
}

BANNER_PORTS = {21, 22, 25, 465, 587, 110, 143, 3306, 6379, 9200}

MAX_HOSTS = 4096


class Module(Module):
    meta = {
        "name": "network/portscan",
        "author": "kitsune",
        "description": "Socket-based TCP port scanner; results are stored into the shared DB",
        "options": {
            "target":  {"default": "", "required": True, "desc": "host or CIDR, e.g. 10.0.0.1 or 192.168.1.0/24"},
            "ports":   {"default": "top", "required": False, "desc": "'top' | range '1-1024' | list '80,443'"},
            "threads": {"default": "200", "required": False, "desc": "concurrency"},
            "timeout": {"default": "1.5", "required": False, "desc": "connect timeout, seconds"},
        },
    }

    def run(self):
        hosts = self._expand_hosts(self.target)
        ports = self._parse_ports(self.ports)
        if not hosts or not ports:
            self.fail("bad target or ports spec")
            return

        timeout = float(self.timeout)
        workers = max(1, min(int(self.threads), 1000))
        self.status(f"hosts={len(hosts)} ports={len(ports)} tasks={len(hosts)*len(ports)} "
                    f"threads={workers} timeout={timeout}s")

        found = []
        tasks = [(h, p) for h in hosts for p in ports]
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(self._probe, h, p, timeout): (h, p) for h, p in tasks}
            total = len(futures)
            for i, fut in enumerate(as_completed(futures), 1):
                if i % 200 == 0:
                    self.status(f"progress {i}/{total}")
                result = fut.result()
                if result:
                    found.append(result)

        if not found:
            self.warn("nothing open found")
            return

        for h, p, svc, banner in found:
            db.add_port(h, p, service=svc, banner=banner)

        self.ok(f"{len(found)} open port(s), written into db")
        rows = [(h, p, svc, banner[:24]) for h, p, svc, banner in found]
        self.table(("Host", "Port", "Service", "Banner"), rows)

    # ------------------------------------------------------------------
    def _probe(self, host: str, port: int, timeout: float):
        """result: (host, port, service, banner) | None"""
        try:
            with socket.create_connection((host, port), timeout=timeout):
                banner = self._grab_banner(host, port)
                return (host, port, SERVICES.get(port, "unknown"), banner)
        except (ConnectionRefusedError, socket.timeout, OSError):
            return None

    @staticmethod
    def _grab_banner(host: str, port: int) -> str:
        if port not in BANNER_PORTS:
            return ""
        try:
            with socket.create_connection((host, port), timeout=1.0) as s:
                s.settimeout(1.0)
                data = s.recv(128)
                return data.decode("utf-8", errors="replace").strip()
        except (OSError,):
            return ""

    @staticmethod
    def _expand_hosts(spec: str) -> list:
        spec = spec.strip()
        try:
            if "/" in spec:
                net = ipaddress.ip_network(spec, strict=False)
                if net.num_addresses > MAX_HOSTS + 2:
                    raise ValueError(f"network too big (>{MAX_HOSTS} hosts)")
                return [str(x) for x in net.hosts()]
            ipaddress.ip_address(spec)
            return [spec]
        except ValueError:
            return []

    @staticmethod
    def _parse_ports(spec: str) -> list:
        spec = spec.strip().lower()
        if spec in ("top", ""):
            return TOP_PORTS
        out = set()
        for part in spec.split(","):
            part = part.strip()
            if "-" in part:
                a, b = part.split("-", 1)
                out.update(range(int(a), int(b) + 1))
            elif part.isdigit():
                out.add(int(part))
        return sorted(out)
