"""web/dirfuzz — брутфорс директорий/файлов (dirb/gobuster-логика, stdlib)."""

import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

from kitsune import db
from kitsune.framework import Module

WORDS = [
    "admin", "admin/", "login", "logout", "dashboard", "wp-admin", "wp-login.php",
    "administrator/", "phpmyadmin/", "mysql/", "index.php", "index.html", "index",
    "robots.txt", "sitemap.xml", ".htaccess", ".env", ".git/", ".git/config",
    ".svn/", "backup/", "backup.sql", "db.sql", "dump.sql", "config.php",
    "wp-config.php", "conf/", "config/", "server-info", "server-status",
    "test", "tmp/", "temp/", "uploads/", "upload/", "files/", "static/",
    "media/", "images/", "js/", "css/", "api/", "api/v1/", "graphql",
    "console/", "shell/", "cmd/", "cgi-bin/", "webdav/", "actuator",
    "user/login", "accounts/", "register", "signup", "cgi-bin/test.cgi",
    "debug", "status", "info.php", "phpinfo.php", "readme.txt", "LICENSE",
]


class Module(Module):
    meta = {
        "name": "web/dirfuzz",
        "author": "kitsune",
        "description": "Bruteforce paths/files on web server (embedded wordlist)",
        "options": {
            "url":      {"default": "", "required": True, "desc": "base url, e.g. http://host/"},
            "threads":  {"default": "20", "required": False, "desc": "concurrency"},
            "timeout":  {"default": "5", "required": False, "desc": "http timeout, seconds"},
            "wordlist": {"default": "", "required": False, "desc": "path to custom wordlist"},
        },
    }

    def run(self):
        base = self.url.strip()
        if not base.endswith("/"):
            base += "/"
        parts = urllib.parse.urlsplit(base)
        if not parts.scheme or not parts.netloc:
            self.fail("need absolute base url, e.g. http://host/")
            return

        words = WORDS
        if self.wordlist:
            try:
                words = [w.strip() for w in open(self.wordlist, encoding="utf-8") if w.strip()]
            except OSError as e:
                self.fail(f"can't read wordlist: {e}")
                return

        self.status(f"fuzzing {len(words)} paths on {parts.netloc}")
        hits = []
        with ThreadPoolExecutor(max_workers=int(self.threads)) as pool:
            futures = {pool.submit(self._check, base, w): w for w in words}
            for fut in as_completed(futures):
                r = fut.result()
                if r:
                    hits.append(r)

        if not hits:
            self.warn("no hits")
            return
        for status, path in hits:
            db.add_loot("web_path", parts.netloc, f"/{path} [{status}]")
        self.ok(f"{len(hits)} hit(s) -> loot")
        self.table(("Path", "Status"), [(p, str(s)) for s, p in hits])

    def _check(self, base, path):
        url = base + path
        req = urllib.request.Request(url, headers={"User-Agent": "kitsune/0.1",
                                                   "referer": base})
        try:
            with urllib.request.urlopen(req, timeout=float(self.timeout)) as resp:
                return (resp.status, path)
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                return (e.code, path)
            return None
        except (urllib.error.URLError, OSError):
            return None
