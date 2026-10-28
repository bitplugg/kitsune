"""web/sqli — детектор error-based SQL инъекций (sqlmap-логика, stdlib)."""

import urllib.error
import urllib.parse
import urllib.request

from kitsune import db
from kitsune.framework import Module

ERROR_SIGNATURES = {
    "mysql":    ["you have an error in your sql syntax", "warning: mysql", "mysqli_", "mysql_fetch"],
    "postgres": ["pg_query", "pg_exec", "unterminated string", "postgresql"],
    "mssql":    ["microsoft sql server", "odbc sql", "unclosed quotation"],
    "oracle":   ["ora-00933", "ora-01756", "quoted string not properly terminated"],
    "sqlite":   ["sqlite", "unterminated string"],
    "generic":  ["syntax error", "jdbc", "hibernate"],
}

PAYLOADS = ["'", ")", "')", '" , "1', "\\"]


class Module(Module):
    meta = {
        "name": "web/sqli",
        "author": "kitsune",
        "description": "Detect error-based SQL injection; hits every URL param with payloads",
        "options": {
            "url":     {"default": "", "required": True, "desc": "URL with params, e.g. http://t/item.php?id=1"},
            "param":   {"default": "", "required": False, "desc": "test a single param (default: all)"},
            "timeout": {"default": "8", "required": False, "desc": "http timeout, seconds"},
        },
    }

    def run(self):
        parts = urllib.parse.urlsplit(self.url.strip())
        if not parts.scheme or not parts.netloc:
            self.fail("need absolute url, e.g. http://host/item.php?id=1")
            return
        params = dict(urllib.parse.parse_qsl(parts.query))
        if not params:
            self.fail("url has no query params to test (add ?param=value)")
            return
        if self.param:
            if self.param not in params:
                self.fail(f"param `{self.param}` not in url")
                return
            params = {self.param: params[self.param]}

        self.status(f"testing {len(params)} param(s) on {parts.netloc}")
        # baseline
        try:
            base_html = self._req(self._url_for(parts, params))[1].lower()
        except OSError as e:
            self.fail(f"target unreachable: {e}")
            return

        findings = []
        for name, value in params.items():
            for payload in PAYLOADS:
                mutated = {**params, name: f"{value}{payload}"}
                try:
                    _, html, _ = self._req(self._url_for(parts, mutated))
                except OSError:
                    continue
                low = html.lower()
                if low == base_html:
                    continue
                for dbms, sigs in ERROR_SIGNATURES.items():
                    if any(s in low for s in sigs):
                        findings.append((name, payload, dbms))
                        break

        if findings:
            for param, payload, dbms in findings:
                db.add_loot("sqli", self.url, f"param={param} payload='{payload}' dbms={dbms}")
            self.ok(f"{len(findings)} SQLi fingerprint(s) -> loot")
            self.table(("Param", "Payload", "DBMS"), findings)
        else:
            self.warn("no SQL error signatures found")

    # ------------------------------------------------------------------
    def _url_for(self, parts, params):
        return urllib.parse.urlunsplit((
            parts.scheme, parts.netloc, parts.path,
            urllib.parse.urlencode(params), parts.fragment,
        ))

    def _req(self, url):
        req = urllib.request.Request(url, headers={"User-Agent": "kitsune/0.1"})
        try:
            with urllib.request.urlopen(req, timeout=float(self.timeout)) as resp:
                return resp.status, resp.read().decode("utf-8", errors="replace"), None
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", errors="replace"), None
