"""Kitsune console — REPL с автодополнением, историей и batch-режимом."""

import readline

from kitsune import art, db, framework

COMMANDS = ["use", "set", "run", "show", "info", "back", "sessions", "interact",
            "setvar", "resource", "report", "dashboard", "doctor", "resetdb",
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
