"""web/xss — детектор reflected XSS (маркеры + фильтры, stdlib)."""

import urllib.error
import urllib.parse
import urllib.request

from kitsune import db
from kitsune.framework import Module

MARKER = "k7snxn"
PAYLOADS = [
    f"<script>{MARKER}(1)</script>",
    f"<img src=x onerror={MARKER}(1)>",
    f'"><script>{MARKER}(1)</script>',
    f"<svg onload={MARKER}(1)>",
]


class Module(Module):
    meta = {
        "name": "web/xss",
        "author": "kitsune",
        "description": "Reflected XSS probe: injects marker payloads into params, checks reflection",
        "options": {
            "url":     {"default": "", "required": True, "desc": "URL with params"},
            "param":   {"default": "", "required": False, "desc": "single param (default: all)"},
            "timeout": {"default": "8", "required": False, "desc": "http timeout"},
        },
    }

    def run(self):
        parts = urllib.parse.urlsplit(self.url.strip())
        if not parts.query:
            self.fail("need url with params (?p=1)")
            return
        params = dict(urllib.parse.parse_qsl(parts.query))
        if self.param:
            if self.param not in params:
                self.fail(f"param `{self.param}` not in url")
                return
            params = {self.param: params[self.param]}

        self.status(f"probing {len(params)} param(s), {len(PAYLOADS)} payloads each")
        findings = []
        for name, value in params.items():
            for payload in PAYLOADS:
                mutated = {**params, name: f"{value}{payload}"}
                url = urllib.parse.urlunsplit((
                    parts.scheme, parts.netloc, parts.path,
                    urllib.parse.urlencode(mutated), parts.fragment,
                ))
                try:
                    _, html = self._req(url)
                except OSError:
                    continue
                if payload in html:
                    findings.append((name, payload[:40]))
                    break  # один payload на парам достаточно для сигнала

        if findings:
            for param, payload in findings:
                db.add_loot("xss", self.url, f"param={param} reflected <{payload}>")
            self.ok(f"{len(findings)} reflected XSS signal(s) -> loot")
            self.table(("Param", "Payload reflected"), findings)
        else:
            self.warn("no reflection found")

    def _req(self, url):
        req = urllib.request.Request(url, headers={"User-Agent": "kitsune/0.1"})
        try:
            with urllib.request.urlopen(req, timeout=float(self.timeout)) as resp:
                return resp.status, resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", errors="replace")
