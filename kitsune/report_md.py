"""Kitsune report builder — markdown + html из общей базы (команда report, api/report)."""

from datetime import datetime

from . import db


def _gather():
    """Данные отчёта одним проходом."""
    return {
        "stats": db.stat(),
        "hosts": [dict(r) for r in db.query("SELECT id, host, hostname FROM hosts ORDER BY id")],
        "ports": [dict(r) for r in db.query(
            "SELECT h.host, p.port, p.service, p.banner FROM ports p "
            "JOIN hosts h ON h.id=p.host_id ORDER BY h.host, p.port")],
        "subs": [dict(r) for r in db.query("SELECT name, ip FROM subdomains ORDER BY name")],
        "sessions": [dict(r) for r in db.list_sessions()],
        "loot": [dict(r) for r in db.query("SELECT id, category, target, data FROM loot ORDER BY id")],
    }


def build_markdown() -> str:
    out = [f"# 🦊 Kitsune session report — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
           "",
           "## Summary",
           "",
           f"| hosts | ports | subdomains | loot | sessions |",
           f"|---|---|---|---|---|"]

    stats = db.stat()
    out.append("| " + " | ".join(str(stats[k]) for k in
                                 ("hosts", "ports", "subdomains", "loot", "sessions")) + " |")
    out.append("")

    hosts = db.query("SELECT id, host, hostname FROM hosts ORDER BY id")
    if hosts:
        out += ["## Hosts", "", "| ID | Host | Hostname |", "|---|---|---|"]
        out += [f"| {h['id']} | `{h['host']}` | {h['hostname']} |" for h in hosts]
        out.append("")
        ports = db.query(
            "SELECT h.host, p.port, p.service, p.banner FROM ports p "
            "JOIN hosts h ON h.id=p.host_id ORDER BY h.host, p.port")
        if ports:
            out += ["## Open ports", "", "| Host | Port | Service | Banner |", "|---|---|---|---|"]
            out += [f"| `{p['host']}` | {p['port']} | {p['service']} | {str(p['banner'])[:40]} |"
                    for p in ports]
            out.append("")

    subs = db.query("SELECT name, ip FROM subdomains ORDER BY name")
    if subs:
        out += ["## Subdomains", "", "| Name | IP |", "|---|---|"]
        out += [f"| {s['name']} | {s['ip']} |" for s in subs]
        out.append("")

    sess = db.list_sessions()
    if sess:
        out += ["## Shell sessions", "", "| id | host | port | status | opened |", "|---|---|---|---|---|"]
        out += [f"| {s['id']} | `{s['host']}` | {s['port']} | {s['status']} | {s['opened_at']} |"
                for s in sess]
        out.append("")

    loot = db.query("SELECT id, category, target, data FROM loot ORDER BY id")
    if loot:
        out += ["## Loot & findings", ""]
        for item in loot:
            out += [f"- **[{item['category']}]** `{item['target']}` — "
                    f"{str(item['data']).replace(chr(10), ' ')[:160]}"]
        out.append("")

    if not hosts and not subs and not loot:
        out += ["(empty session — ничего не найдено)", ""]

    return "\n".join(out) + "\n"

_CSS = """
body{font-family:ui-monospace,monospace;max-width:960px;margin:24px auto;padding:0 16px;
     background:#0d1117;color:#c9d1d9}
h1{color:#ff8a1f}h2{border-bottom:1px solid #30363d;padding-bottom:4px}
table{border-collapse:collapse;margin:8px 0 18px}
th,td{border:1px solid #30363d;padding:4px 10px;text-align:left}
th{background:#161b22;color:#ff8a1f}
code{color:#7ee787}tr:nth-child(even){background:#161b22}
.empty{color:#8b949e;font-style:italic}
ul.loot li{margin:4px 0}
"""


def build_html() -> str:
    import html as _h
    d = _gather()
    st = d["stats"]
    esc = lambda s: _h.escape(str(s))
    out = [
        "<!doctype html><html><head><meta charset='utf-8'>",
        "<title>Kitsune report</title>",
        f"<style>{_CSS}</style></head><body>",
        f"<h1>🦊 Kitsune session report</h1>",
        f"<p><em>{_h.escape(datetime.now().strftime('%Y-%m-%d %H:%M'))}</em></p>",
        "<h2>Summary</h2><table><tr>"
        + "".join(f"<th>{k}</th>" for k in ("hosts", "ports", "subdomains", "loot", "sessions"))
        + "</tr><tr>"
        + "".join(f"<td>{st.get(k, 0)}</td>"
                  for k in ("hosts", "ports", "subdomains", "loot", "sessions"))
        + "</tr></table>",
    ]

    def table(title, headers, rows):
        if not rows:
            return
        out.append(f"<h2>{_h.escape(title)}</h2><table><tr>")
        out.extend(f"<th>{_h.escape(h)}</th>" for h in headers)
        out.append("</tr>")
        for r in rows:
            out.append("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>")
        out.append("</table>")

    table("Hosts", ("ID", "Host", "Hostname"),
          [(h["id"], h["host"], h["hostname"] or "") for h in d["hosts"]])
    table("Open ports", ("Host", "Port", "Service", "Banner"),
          [(p["host"], p["port"], p["service"], (p["banner"] or "")[:40]) for p in d["ports"]])
    table("Subdomains", ("Name", "IP"), [(s["name"], s["ip"] or "") for s in d["subs"]])
    table("Shell sessions", ("id", "host", "port", "status", "opened"),
          [(s["id"], s["host"], s["port"], s["status"], s["opened_at"]) for s in d["sessions"]])

    if d["loot"]:
        out.append("<h2>Loot &amp; findings</h2><ul class='loot'>")
        for item in d["loot"]:
            data = esc(item["data"]).replace("\n", " ")[:160]
            out.append(f"<li><b>[{esc(item['category'])}]</b> "
                       f"<code>{esc(item['target'])}</code> — {data}</li>")
        out.append("</ul>")

    if not d["hosts"] and not d["subs"] and not d["loot"]:
        out.append("<p class='empty'>(пустой скан — рез-тов не найдено)</p>")
    out.append("</body></html>")
    return "\n".join(out)
