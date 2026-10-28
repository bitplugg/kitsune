"""web/techdetect — fingerprint веб-сервера по заголовкам и HTML (wappalyzer-lite)."""

import urllib.request
import urllib.error

from kitsune import db
from kitsune.framework import Module


class Module(Module):
    meta = {
        "name": "web/techdetect",
        "author": "kitsune",
        "description": "Fingerprint web server stack from headers + html title",
        "options": {
            "url":     {"default": "", "required": True, "desc": "absolute URL"},
            "timeout": {"default": "8", "required": False, "desc": "http timeout"},
        },
    }

    def run(self):
        try:
            req = urllib.request.Request(self.url, headers={"User-Agent": "kitsune/0.1"})
            with urllib.request.urlopen(req, timeout=float(self.timeout)) as resp:
                status = resp.status
                headers = dict(resp.headers)
                html = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            status, headers, html = e.code, dict(e.headers), e.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, OSError) as e:
            self.fail(f"unreachable: {e}")
            return

        rows = [("HTTP status", str(status))]
        for h in ("Server", "X-Powered-By", "X-AspNet-Version", "X-Generator",
                  "Via", "X-Drupal-Cache", "X-Shopify-Stage"):
            if h in headers:
                rows.append((h, headers[h][:60]))
        if "Set-Cookie" in headers:
            rows.append(("Set-Cookie", headers["Set-Cookie"][:60]))

        title = ""
        if "<title" in html.lower():
            try:
                title = html.lower().split("<title", 1)[1].split(">", 1)[1].split("<", 1)[0].strip()
            except IndexError:
                pass
        if title:
            rows.append(("Page title", title[:60]))

        gen = [m for m in ("/wp-content/", "wordpress", "/sites/default/",
                           "django", "laravel_session", "JSESSIONID", "phpsessid",
                           "express", "starterkit=", "generator\"")
               if m.lower() in html.lower()]
        if gen:
            rows.append(("HTML hints", ", ".join(gen[:6])))

        db.add_loot("tech", self.url, "; ".join(f"{k}={v}" for k, v in rows))
        self.ok("fingerprint stored in loot")
        self.table(("Field", "Value"), rows)
