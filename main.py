#!/usr/bin/env python3
"""kitsune — CLI entrypoint (обёртка над kitsune.cli).

  python main.py                    # интерактивный REPL
  python main.py --version
  python main.py -c 'stats; show modules'
  python main.py --resource etc/example_chain.rc
"""

from kitsune.cli import main

if __name__ == "__main__":
    main()
