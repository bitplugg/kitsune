"""Kitsune framework — реестр модулей, параметры, вывод."""

import importlib
import pkgutil
import socket

from . import db

_dim = "\033[2m"
_bold = "\033[1m"
_red = "\033[31m"
_yellow = "\033[33m"
_orange = "\033[38;5;208m"
_green = "\033[32m"
_reset = "\033[0m"

BANNER = (
    _yellow + r"""
  _  _____ _   _ _
 | |/ /_ _| \ | | |
 | ' / | ||  \| | |
 | . \ | || |\  | |___
 |_|\_\___|_| \_|_____|  v0.1.0 "Nebula"
""" + _reset
    + _dim + "     the nine-tailed pentest framework\n" + _reset
    + _orange + "  [!]" + _reset + " use authorized targets only\n"
)

HELP = """
  use <module>        загрузить модуль (например: use network/portscan)
  set <opt> <value>   установить опцию активного модуля
  run                 запустить активный модуль
  info                описание активного модуля
  back                выгрузить модуль
  setvar <n> <v>      переменная для resource (подставляется как ${n})
  resource <file.rc>  выполнить цепочку REPL-команд из файла
  sessions            список живых shell-сессий
  interact <id>       взять управление над shell'ом
  doctor              проверить окружение (python/scapy/sTools/net/db)
  resetdb [yes]       очистить базу сессии (подтверждение `yes` обязательн)
  show modules        список модулей
  show hosts|ports|subdomains|loot|options
  report [file.md]    сгенерировать markdown отчёт из базы
  dashboard           TUI-обзор (q для выхода)
  stats               счётчики базы
  clear               очистить экран
  exit                выход
"""


class Module:
    """Базовый класс модуля."""

    meta: dict = {}

    def __init__(self, fw):
        self.fw = fw
        for key, opt in self.meta.get("options", {}).items():
            setattr(self, key, str(opt.get("default", "")))

    # хелперы вывода, доступные модулям
    @property
    def print(self):
        return self.fw.print

    def ok(self, s):    self.fw.ok(s)
    def fail(self, s):  self.fw.fail(s)
    def warn(self, s):  self.fw.warn(s)
    def status(self, s): self.fw.status(s)
    def table(self, headers, rows): self.fw.table(headers, rows)


class Framework:
    """Реестр + диспетчер команд REPL."""

    def __init__(self):
        self.modules: dict[str, type] = {}
        self.active: Module | None = None
        self.sessions: list[dict] = []   # живые reverse-shell сессии
        self.vars: dict[str, str] = {}   # переменные для resource-скриптов
        self.load_modules()

    # --- вывод ------------------------------------------------------
    @staticmethod
    def print(msg: str = ""):
        print(f"  {msg}")

    @staticmethod
    def ok(msg):    print(f"  {_green}[+]{_reset} {msg}")
    @staticmethod
    def fail(msg):  print(f"  {_red}[-]{_reset} {msg}")
    @staticmethod
    def warn(msg):  print(f"  {_yellow}[!]{_reset} {msg}")
    @staticmethod
    def status(msg): print(f"  {_orange}[*]{_reset} {msg}")

    @staticmethod
    def table(headers: tuple, rows: list):
        if not rows:
            Framework.print(_dim + "(empty)" + _reset)
            return
        widths = [
            max(max(len(str(r[i])) for r in rows), len(h))
            for i, h in enumerate(headers)
        ]
        head = "     " + "  ".join(str(h).ljust(w) for h, w in zip(headers, widths))
        sep = "     " + "  ".join("-" * w for w in widths)
        print(_bold + head + _reset)
        print(_dim + sep + _reset)
        for r in rows:
            print("     " + "  ".join(str(c).ljust(w)[:w] for c, w in zip(r, widths)))

    # --- загрузка модулей -------------------------------------------
    def load_modules(self):
        import kitsune.modules as pkg
        for m in pkgutil.walk_packages(pkg.__path__, prefix=f"{pkg.__name__}."):
            if m.ispkg:
                continue
            mod = importlib.import_module(m.name)
            if hasattr(mod, "Module"):
                cls = mod.Module
                self.modules[cls.meta.get("name", m.name)] = cls

    # --- внутренние --------------------------------------------------
    def _check_active(self) -> bool:
        if self.active is None:
            self.fail("no active module — сначала `use <module>`")
            return False
        return True

    # --- команды ------------------------------------------------------
    def cmd_use(self, args):
        if not args:
            self.fail("usage: use <module>")
            return
        name = args[0]
        if name in self.modules:
            matches = [name]
        else:
            matches = [n for n in self.modules if n.endswith(f"/{name}")]
        if not matches:
            self.fail(f"module not found: {name}")
            return
        if len(matches) > 1:
            self.fail(f"ambiguous: {', '.join(matches)}")
            return
        self.active = self.modules[matches[0]](self)
        self.ok(f"loaded {matches[0]}")

    def cmd_set(self, args):
        if len(args) < 2:
            self.fail("usage: set <option> <value>")
            return
        if not self._check_active():
            return
        key, value = args[0], " ".join(args[1:])
        allowed = self.active.meta.get("options", {})
        if key not in allowed:
            self.fail(f"unknown option `{key}` — available: {', '.join(allowed)}")
            return
        setattr(self.active, key, value)
        self.ok(f"{key} => {value}")

    def cmd_run(self, _):
        if not self._check_active():
            return
        opts = self.active.meta.get("options", {})
        missing = [k for k, o in opts.items() if o.get("required") and not getattr(self.active, k)]
        if missing:
            self.fail(f"set options first: {', '.join(missing)}")
            return
        self.status(f"running {self.active.meta.get('name')} ...")
        try:
            self.active.run()
        except KeyboardInterrupt:
            self.warn("interrupted")
        except Exception as e:  # noqa: BLE001
            self.fail(f"module error: {e}")

    def cmd_show(self, args):
        what = args[0] if args else "modules"
        if what == "options" and self.active:
            opts = self.active.meta.get("options", {})
            rows = [
                (k, getattr(self.active, k, ""), "yes" if o.get("required") else "", o.get("desc", ""))
                for k, o in opts.items()
            ]
            self.table(("Option", "Value", "Req", "Description"), rows)
            return
        if self.active and what == "info":
            self.cmd_info(None)
            return
        if what == "all":
            for sub in ("hosts", "ports", "subdomains", "sessions", "loot"):
                print(_dim + f"  --- {sub} ---" + _reset)
                self.cmd_show([sub])
                print()
            return
        if what == "modules":
            self.table(("Module", "Description"), [
                (n, cls.meta.get("description", "")) for n, cls in sorted(self.modules.items())
            ])
            return
        if what == "sessions":
            hist = db.list_sessions()
            self.table(("DB id", "Host", "Port", "State", "Opened"),
                       [(h["id"], h["host"], h["port"], h["status"], h["opened_at"])
                        for h in hist])
            return
        if what == "hosts":
            rows = [(r["id"], r["host"], r["hostname"], r["os_guess"])
                    for r in db.query("SELECT * FROM hosts ORDER BY id")]
            self.table(("ID", "Host", "Hostname", "OS"), rows)
            return
        if what == "ports":
            rows = [(r["id"], r["host"], r["port"], r["proto"], r["service"])
                    for r in db.query(
                        "SELECT p.id, h.host, p.port, p.proto, p.service "
                        "FROM ports p JOIN hosts h ON h.id=p.host_id ORDER BY h.host, p.port")]
            self.table(("ID", "Host", "Port", "Proto", "Service"), rows)
            return
        if what == "subdomains":
            rows = [(r["name"], r["ip"]) for r in
                    db.query("SELECT name, ip FROM subdomains ORDER BY name")]
            self.table(("Subdomain", "IP"), rows)
            return
        if what == "loot":
            rows = [(r["id"], r["category"], r["target"], str(r["data"])[:64])
                    for r in db.query("SELECT * FROM loot ORDER BY id")]
            self.table(("ID", "Category", "Target", "Data"), rows)
            return
        self.fail(f"unknown show target: {what}")

    def cmd_info(self, _):
        if not self._check_active():
            return
        m = self.active.meta
        print(_bold + f"\n    {m.get('name')}" + _reset)
        print(_dim + f"    author: {m.get('author', 'unknown')}" + _reset)
        print(f"    {m.get('description', '')}\n")

    def cmd_back(self, _):
        if self.active:
            self.ok(f"unloaded {self.active.meta.get('name')}")
            self.active = None

    def cmd_setvar(self, args):
        """Установить переменную для resource-скриптов: setvar target 10.0.0.1"""
        if len(args) < 2:
            self.fail("usage: setvar <name> <value>")
            return
        name, value = args[0], " ".join(args[1:])
        self.vars[name] = value
        self.ok(f"${{{name}}} => {value}")

    def _subst(self, text: str) -> str:
        """Подставить ${var} из self.vars (пустая строка если var не задан)."""
        import re
        for name in set(re.findall(r"\$\{(\w+)\}", text)):
            text = text.replace("${" + name + "}", self.vars.get(name, ""))
        return text

    def cmd_resource(self, args):
        """Выполнить файл-цепочку REPL-команд (переменные ${var} подставляются)."""
        if not args:
            self.fail("usage: resource <file.rc>")
            return
        path = args[0]
        try:
            lines = open(path, encoding="utf-8").read().splitlines()
        except OSError as e:
            self.fail(f"can't read resource: {e}")
            return
        self.status(f"executing resource {path} ({len(lines)} lines)")
        for line in lines:
            line = self._subst(line.strip())
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if parts[0] in ("exit", "quit"):
                self.warn("resource: stop at `exit`")
                break
            handler = getattr(self, f"cmd_{parts[0]}", None)
            if handler is None:
                self.fail(f"[resource] unknown command: {parts[0]}")
                continue
            try:
                handler(parts[1:])
            except SystemExit:
                raise

    def cmd_report(self, args):
        """Сгенерировать markdown/html отчёт из общей базы."""
        from datetime import datetime
        from kitsune import report_md
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = args[0] if args else f"kitsune_report_{stamp}.md"
        if path.lower().endswith(".html"):
            content = report_md.build_html()
        else:
            content = report_md.build_markdown()
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        self.ok(f"report written: {path} ({path.rsplit('.', 1)[-1].upper()} format)")
        self.warn("keep it OUT of public repos (contains loot!)")

    def cmd_sessions(self, _):
        """Список живых сессий (из памяти) + история из db."""
        if self.sessions:
            rows = [(i, s["host"], s["port"], "LIVE") for i, s in enumerate(self.sessions)]
            self.ok(f"{len(self.sessions)} live shell session(s) — `interact <id>`")
            self.table(("Idx", "Host", "Port", "State"), rows)
        else:
            self.print(_dim + "(no live sessions in memory)" + _reset)
        hist = db.list_sessions()
        if hist:
            self.table(("DB id", "Host", "Port", "State", "Opened"),
                       [(h["id"], h["host"], h["port"], h["status"], h["opened_at"])
                        for h in hist])

    def cmd_interact(self, args):
        """Взять управление над живой сессией."""
        if not self.sessions:
            self.fail("no live sessions — настоящему шеллу нужен payloads/listener")
            return
        try:
            idx = int(args[0]) if args else len(self.sessions) - 1
            sess = self.sessions[idx]
        except (IndexError, ValueError):
            self.fail(f"session index 0..{len(self.sessions)-1}")
            return

        conn = sess["conn"]
        self.ok(f"interacting with {sess['host']}:{sess['port']} — `exit` to leave")
        while True:
            try:
                cmd = input("kitsune (shell) > ")
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not cmd:
                continue
            if cmd in ("exit", "quit", "q"):
                break
            try:
                conn.sendall(cmd.encode() + b"\n")
            except OSError as e:
                self.fail(f"connection lost: {e}")
                self.sessions.pop(idx)
                db.close_session(sess.get("db_id", 0))
                return
            buf = b""
            conn.settimeout(1.5)
            try:
                while True:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    buf += chunk
            except socket.timeout:
                pass
            except OSError as e:
                self.fail(f"connection lost: {e}")
                self.sessions.pop(idx)
                db.close_session(sess.get("db_id", 0))
                return
            if buf:
                for line in buf.decode("utf-8", errors="replace").splitlines():
                    self.print(line)

    def cmd_stats(self, _):
        self.table(("Table", "Rows"), [(k, str(v)) for k, v in db.stat().items()])
        print(_dim + f"     db: {db.DB_PATH}" + _reset)

    def cmd_dashboard(self, _):
        """TUI-обзор (curses): статистика, модули, loot."""
        import curses
        import random
        from kitsune import art, tui

        tagline = random.choice(art.TAGLINES)
        try:
            curses.wrapper(tui.main_loop, self.modules, tagline)
        except (curses.error, OSError) as e:
            self.fail(f"TUI недоступен тут: {e} (нужен настоящий терминал)")
        self.print()

    def cmd_doctor(self, _):
        """Проверка окружения: зависимости, тулзы, сеть, база."""
        import os
        import shutil
        import socket
        import sys

        rows = []
        ver = sys.version_info
        rows.append(("python", f"{ver.major}.{ver.minor}.{ver.micro}",
                     "ok" if (ver.major, ver.minor) >= (3, 9) else "need >=3.9"))

        try:
            import scapy  # noqa: F401
            rows.append(("scapy", "installed", "ok (wireless modules available)"))
        except ImportError:
            rows.append(("scapy", "missing", "pip3 install scapy для wireless/*"))

        for tool, note in (("ip", "wireless/monitor"), ("iw", "wireless/monitor"),
                           ("nmap", "не обязателен"), ("hashcat", "не обязателен")):
            path = shutil.which(tool)
            rows.append((tool, path or "missing", note if not path else f"found {note}"))

        try:
            socket.create_connection(("services.nvd.nist.gov", 443), timeout=4).close()
            rows.append(("internet", "reachable", "ok (cve_search / crtsh будут работать)"))
        except OSError as e:
            rows.append(("internet", "blocked", f"offline ({e.__class__.__name__})"))

        try:
            db_dir = os.path.dirname(db.DB_PATH)
            os.makedirs(db_dir, exist_ok=True)
            probe = os.path.join(db_dir, ".write_probe")
            with open(probe, "w") as f:
                f.write("1")
            os.remove(probe)
            rows.append(("session db", db.DB_PATH, "writable"))
        except OSError as e:
            rows.append(("session db", db.DB_PATH, f"NOT writable: {e}"))

        self.ok("environment check:")
        self.table(("Check", "Value", "Note"), rows)

    def cmd_resetdb(self, args):
        """Сброс сессии; требует подтверждения: `resetdb yes`."""
        import os
        if args and args[0] == "yes":
            try:
                os.remove(db.DB_PATH)
                db._local.conn = None  # noqa: SLF001
                self.sessions.clear()
                self.ok(f"session db wiped: {db.DB_PATH}")
            except FileNotFoundError:
                self.warn("already empty")
            except OSError as e:
                self.fail(f"reset failed: {e}")
            return
        self.warn("this clears ALL hosts/loot/sessions; confirm: `resetdb yes`")
        self.cmd_stats(None)

    def cmd_exit(self, _):
        raise SystemExit(0)
