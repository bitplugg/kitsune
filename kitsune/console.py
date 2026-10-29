"""Kitsune console — REPL с автодополнением, историей и batch-режимом."""

import readline

from kitsune import art, db, framework

COMMANDS = ["use", "set", "run", "show", "info", "back", "sessions", "interact",
            "setvar", "resource", "wizard", "report", "dashboard", "doctor", "resetdb",
            "stats", "help", "clear", "exit"]
SHOW_ITEMS = ["modules", "hosts", "ports", "subdomains", "sessions", "loot", "options", "all"]


def _make_completer(fw: framework.Framework):
    def completer(text, state):
        line = readline.get_line_buffer()
        parts = line.split()
        if not parts or (len(parts) == 1 and not line.endswith(" ")):
            opts = [c for c in COMMANDS if c.startswith(text)]
        elif parts[0] == "use":
            opts = [m for m in fw.modules if m.startswith(text)]
        elif parts[0] == "show":
            opts = [s for s in SHOW_ITEMS if s.startswith(text)]
        elif parts[0] == "set" and fw.active:
            opts = [k for k in fw.active.meta.get("options", {}) if k.startswith(text)]
        elif parts[0] == "setvar":
            opts = list(fw.vars)
        else:
            opts = []
        matches = sorted(opts)
        return matches[state] if state < len(matches) else None
    return completer


def _dispatch(fw, line: str) -> str:
    """Выполнить строку. Возвращает 'exit' | '' (используется и REPL-ом, и batch-ом)."""
    line = fw._subst(line.strip())  # noqa: SLF001
    if not line:
        return ""
    cmd, *args = line.split()
    if cmd in ("exit", "quit", "q"):
        return "exit"
    handler = getattr(fw, f"cmd_{cmd}", None)
    if handler:
        try:
            handler(args)
        except SystemExit:
            return "exit"
    elif cmd == "help" or cmd == "?":
        fw.print(framework.HELP)
    elif cmd == "clear":
        print("\033[2J\033[H", end="")
    else:
        fw.fail(f"unknown command `{cmd}` — try `help`")
    return ""


def banner(fw):
    print(art.random_banner(list(fw.modules)))
    stats = db.stat()
    print(framework._dim)  # noqa: SLF001
    print(f"   db rows: {stats}   session: {db.DB_PATH}")
    print(framework._reset)


# ------------------------------------------------------------------ wizard
def _ask(prompt, default=""):
    try:
        val = input(f"  {prompt}").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        val = ""
    return val or default


def _runline(fw, line):
    _dispatch(fw, line)


def wizard(fw):
    """sqlmap --wizard-стиль: дружелюбное меню, собирающее workflow из модулей."""
    print()
    fw.status("setup wizard — выбери рабочий процесс")
    print(framework._dim + """
   [1] network scan    — discovery + portscan по IP/CIDR
   [2] web audit       — techdetect + dirfuzz (+sqli, если есть ?param)
   [3] wireless        — monitor → scan → (по желанию) deauth
   [4] recon           — subdomain + dnsenum по домену
   [q] продолжить руками (REPL)
""" + framework._reset)  # noqa: SLF001

    choice = _ask("  выбор [1]: ", "1")

    if choice == "1":
        target = _ask("  target (IP или CIDR) [192.168.1.0/24]: ", "192.168.1.0/24")
        _runline(fw, "use discovery")
        _runline(fw, f"set target {target}")
        _runline(fw, "run")
        _runline(fw, "back")
        ports = _ask("  порты [top]: ", "top")
        _runline(fw, "use portscan")
        _runline(fw, f"set target {target}")
        _runline(fw, f"set ports {ports}")
        _runline(fw, "run")
        _runline(fw, "back")

    elif choice == "2":
        url = _ask("  базовый url (например http://10.0.0.5/): ", "")
        if not url:
            fw.warn("url не задан — пропуск web-этапа")
        else:
            for mod in ("techdetect", "dirfuzz"):
                _runline(fw, f"use {mod}")
                _runline(fw, f"set url {url}")
                _runline(fw, "run")
                _runline(fw, "back")
        squrl = _ask("  url с ?param для sqli (опционально): ", "")
        if squrl:
            _runline(fw, "use sqli")
            _runline(fw, f"set url {squrl}")
            _runline(fw, "run")
            _runline(fw, "back")

    elif choice == "3":
        iface = _ask("  iface [wlan0]: ", "wlan0")
        channel = _ask("  канал для scan (пусто = hop 1..13): ", "")
        _runline(fw, "use monitor")
        _runline(fw, f"set iface {iface}")
        _runline(fw, "run")
        _runline(fw, "back")
        _runline(fw, "use scan")
        _runline(fw, f"set iface {iface}")
        if channel:
            _runline(fw, f"set channel {channel}")
        _runline(fw, "set seconds 30")
        _runline(fw, "run")
        _runline(fw, "back")
        if _ask("  deauth-тест? (y/[N]): ", "").lower().startswith("y"):
            bssid = _ask("  bssid цели: ", "")
            client = _ask("  client [broadcast]: ", "broadcast")
            count = _ask("  кадры [10]: ", "10")
            _runline(fw, "use deauth")
            _runline(fw, f"set iface {iface}")
            _runline(fw, f"set bssid {bssid}")
            _runline(fw, f"set client {client}")
            _runline(fw, f"set count {count}")
            _runline(fw, "run")
            _runline(fw, "back")

    elif choice == "4":
        domain = _ask("  domain: ", "")
        if domain:
            _runline(fw, "use subdomain")
            _runline(fw, f"set domain {domain}")
            _runline(fw, "run")
            _runline(fw, "back")
            _runline(fw, "use dnsenum")
            _runline(fw, f"set domain {domain}")
            _runline(fw, "run")
            _runline(fw, "back")

    _runline(fw, "stats")
    if _ask("  сгенерировать отчёт? (y/[N]): ", "").lower().startswith("y"):
        name = _ask("  имя [kitsune_wizard_report.md]: ", "kitsune_wizard_report.md")
        _runline(fw, f"report {name}")
    fw.warn("для showcasing: `show all` / `dashboard`; с переменными: `resource`")


def wizard_session():
    fw = framework.Framework()
    banner(fw)
    wizard(fw)
    fw.status("bye. 🦊")


def main():
    fw = framework.Framework()

    readline.set_completer(_make_completer(fw))
    readline.set_completer_delims(" \t\n")
    readline.parse_and_bind("tab: complete")

    banner(fw)

    while True:
        if fw.active:
            name = fw.active.meta.get("name", "")
            prompt = f"\nkitsune ({name}) > "
        else:
            prompt = "\nkitsune > "
        try:
            line = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if _dispatch(fw, line) == "exit":
            break

    fw.status("bye. 🦊")


def batch(commands: list):
    """CLI-режим: выполнить список команд без интеракции и выйти."""
    fw = framework.Framework()
    banner(fw)
    for line in commands:
        if _dispatch(fw, line) == "exit":
            break
    fw.status("done. 🦊")


if __name__ == "__main__":
    main()
