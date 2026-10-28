#!/usr/bin/env bash
# kitsone installer: venv + editable install + kitsune в PATH
set -euo pipefail
cd "$(dirname "$0")"

python3 -m venv .venv 2>/dev/null || true
source .venv/bin/activate
pip install -e . -q

if [ -w /usr/local/bin ] || [ "$(id -u)" = "0" ]; then
  ln -sf "$(pwd)/.venv/bin/kitsune" /usr/local/bin/kitsune
  echo "[+] installed: kitsune (щmoj запускайте из любой точки)"
else
  echo "[!] нет прав на /usr/local/bin — добавьте в PATH: export PATH=\"$(pwd)/.venv/bin:\$PATH\""
fi

kitsune --version
echo "[+] готово: kitsune"
