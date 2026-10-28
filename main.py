#!/usr/bin/env python3
"""kitsune — CLI entrypoint.

  python main.py                     # интерактивный REPL
  python main.py --version
  python main.py -c 'stats; show modules'
  python main.py --resource etc/example_chain.rc
"""

import argparse
import sys

from kitsune import __version__


def build_parser():
    p = argparse.ArgumentParser(
        prog="kitsune",
        description="🦊 nine-tailed pentest framework",
        epilog="authorized targets only",
    )
    p.add_argument("--version", action="version", version=f"kitsune {__version__}")
    p.add_argument("-c", "--cmd", metavar="CMDS",
                   help="выполнить команды (разделитель `;`) и выйти, "
                        "например: -c 'use doctor; run'")
    p.add_argument("--resource", metavar="FILE",
                   help="выполнить chain-файл (.rc) и выйти")
    return p


def main():
    args = build_parser().parse_args()

    if args.resource:
        sys.path.insert(0, "")
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
