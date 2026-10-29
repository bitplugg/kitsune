"""kitsune.cli — точка входа команды: разбор флагов и запуск REPL / batch."""

import argparse
import sys

from kitsune import __version__


def build_parser():
    p = argparse.ArgumentParser(
        prog="kitsune",
        description="🦊 nine-tailed pentest framework",
        epilog="authorized targets only; use `kitsune` alone for the interactive REPL",
    )
    p.add_argument("--version", action="version", version=f"kitsune {__version__}")
    p.add_argument("-w", "--wizard", action="store_true",
                   help="интерактивный brother (как sqlmap --wizard): guided scan")
    p.add_argument("-c", "--cmd", metavar="CMDS",
                   help="выполнить команды (разделитель `;`) и выйти, "
                        "например: kitsune -c 'use doctor; run'")
    p.add_argument("--resource", metavar="FILE",
                   help="выполнить chain-файл (.rc) и выйти")
    return p


def main():
    args = build_parser().parse_args()

    if args.wizard:
        from kitsune import console
        console.wizard_session()
        return

    if args.resource:
        from kitsune import console
        console.batch([f"resource {args.resource}"])
        return

    if args.cmd:
        from kitsune import console
        cmds = [c.strip() for c in args.cmd.split(";") if c.strip()]
        console.batch(cmds)
        return

    from kitsune import console
    console.main()


if __name__ == "__main__":
    main()
