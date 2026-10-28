# 🦊 kitsune

```
  _  _____ _   _ _
 | |/ /_ _| \ | | |
 | ' / | ||  \| | |
 | . \ | || |\  | |___
 |_|\_\___|_| \_|_____|  v0.1.0 "Nebula"
```

**Nine-tailed pentest framework** — единый CLI на стыке nmap / metasploit /
aircrack-ng / routersploit / sqlmap. Всё пишут в **общую SQLite-базу сессии**, поэтому
результаты одного модуля автоматически становятся входом для следующего:
`hosts → ports → subdomains → loot`.

## Установка

```bash
# вариант 1 — как системная команда (recommended):
pipx install --editable /path/to/kitsune     # → бинарь `kitsune` в PATH

git clone https://github.com/bitplugg/kitsune.git ~/kitsune
pipx install --editable ~/kitsune
kitsune --version     # kitsune 0.1.0

# вариант 2 — классический venv:
bash install.sh       # venv + pip install -e . + линк в /usr/local/bin

# вариант 3 — без установки:
python3 main.py
```

# CLI-режимы

```bash
kitsune                                              # интерактивный REPL
kitsune --version
kitsune -c 'use doctor; run'                        # одиночная команда
kitsune -c 'use portscan; set target 127.0.0.1; run; stats'
kitsune --resource etc/example_chain.rc             # chain-файл
```

## Запуск

```bash
cd kitsune
python3 main.py          # REPL со случайным ASCII-бannером
```

## Сессия

```
kitsune > use portscan
kitsune (network/portscan) > set target 192.168.1.0/24
kitsune (network/portscan) > set ports 1-1000
kitsune (network/portscan) > run
kitsune (network/portscan) > back

kitsune > use subdomain
kitsune (recon/subdomain) > set domain example.com
kitsune (recon/subdomain) > run

kitsune > show hosts
kitsune > show ports
kitsune > show subdomains
kitsune > stats
```

## Команды ключевые

```
use / set / run / info / back      работа с модулем (автодополнение tab)
show modules|hosts|ports|subdomains|sessions|loot|all
sessions / interact <id>           живые reverse-shell сессии
resource <file.rc> / setvar        chain-автоматизация
report <file.md|file.html>         отчёты
dashboard                          TUI-обзор
doctor / resetdb [yes] / stats     обслуживание сессии
```

## Тесты

```bash
python3 -m unittest discover -s tests -v    # 14 тестов (db, framework, helpers)
```

## 📘 Wiki

Полная документация по каждому модулю (примеры, все опции, таблицы,
development-гайд) — [*wiki*](https://bitplugg.github.io/kitsune/wiki.html)
на GitHub Pages (исходники: `docs/00-overview.md` ... `docs/10-development.md`).

## Модули

| Модуль | Аналог | Сложность | Статус |
|---|---|---|---|
| `web/sqli` | sqlmap | 🔴 сложно | ✅ |
| `exploits/web/sqli_union` | sqlmap (union) | 🔴 сложно | ✅ |
| `wireless/scan` | airodump-ng | 🔴 сложно | ✅ (scapy) |
| `wireless/deauth` | mdk4/aireplay | 🔴 сложно | ✅ (scapy) |
| `payloads/listener` | msf handler + `sessions`/`interact` | 🔴 сложно | ✅ |
| `exploits/cve_search` | searchsploit (NVD API) | 🟢 легко | ✅ |
| `payloads/bind_shell` | msfvenom bind_tcp | ⚪ легчайшее | ✅ |
| `dashboard` (TUI) | metasploit table UI | 🟡 нормально | ✅ |
| `post/enum` | msf post | 🟡 нормально | ✅ |
| `post/exfil` | exfil файла через shell | 🟡 нормально | ✅ |
| `api/serve` | msf RPC (REST) | 🟢 легко | ✅ |
| `team/sync` | team server / share | 🟡 нормально | ✅ |
| `wireless/monitor` | airmon-ng | 🟢 легко | ✅ |
| `report` (md + **html**) | faraday/метa | 🟢 легко | ✅ |
| `exploits/web/shellshock` | CVE-2014-6271 | 🔴 сложно | ✅ |
| `exploits/web/path_traversal` | LFI prbe | 🟡 нормально | ✅ |
| `exploits/router/auth_bypass` | routersploit | 🟡 нормально | ✅ |
| `web/dirfuzz` | dirb/gobuster | 🟡 нормально | ✅ |
| `web/xss` | XSStrike | 🟡 нормально | ✅ |
| `network/discovery` | arp-scan | 🟡 нормально | ✅ |
| `web/techdetect` | wappalyzer | 🟢 легко | ✅ |
| `recon/crtsh` | certspotter | 🟢 легко | ✅ |
| `recon/dnsenum` | dnsrecon | 🟢 легко | ✅ |
| `recon/whois` | whois | ⚪ легчайшее | ✅ |
| `payloads/reverse_shell` | msfvenom | ⚪ легчайшее | ✅ |
| `network/portscan` | nmap | ⚪ легчайшее | ✅ |
| `recon/subdomain` | dnsrecon | ⚪ легчайшее | ✅ |

## Правовая оговорка

Используйте только на сетях и системах, на которые у вас есть **явное разрешение**
(ваша лаборатория, целевая инфраструктура по договору, ctf-стенды).

## Отчёт

```
kitsune > report my_scan.md    # markdown таблицы (hosts/ports/loot)
kitsune > report my_scan.html  # красиво оформленный HTML (тёмная тема)
```

## Chain-DSL (resource-скрипты)

Автоматизация пентеста — файл с REPL-командами + переменные:

```
kitsune > setvar target 192.168.1.50
kitsune > resource etc/example_chain.rc
```

```bash
# etc/example_chain.rc
setvar target 127.0.0.1
use portscan
set target ${target}      # подставится из setvar!
run
back
use techdetect
set url http://${target}:8803/
run
report kitsune_chain_report.md
```

## TUI-дашборд

```
kitsune > dashboard       # curses UI: статистика, группы модулей, hosts, loot
                          # q — выйти
```

## Дорожная карта (статус)

- ✅ recon → network → web → exploits → payloads → post (полный цикл)
- ✅ resource-детали, live-sessions, team-sync, REST API, TUI, отчёты (md+html)
- ✅ `pipx install` → системный бинарь `kitsune` (CLI-флаги -c / --resource)
- 📋 chain-checkpoints (промежуточный save-/load state между шагами)
- 📋 GUI-клиент поверх REST api
- 📋 PyPI-публикация (pip install kitsune)

## Структура

```
kitsune/
├── main.py                  CLI: REPL / -c / --resource
├── kitsune/
│   ├── console.py           REPL + batch
│   ├── framework.py         реестр модулей, команды, reporter
│   ├── db.py                общая SQLite сессии
│   ├── report_md.py         markdown + HTML рендеры
│   ├── tui.py               curses-дашборд
│   ├── art.py               случайные ASCII-баннеры 🎲
│   └── modules/             10 пакетов, 25 модулей
├── tests/test_kitsune.py    14 unittest-тестов
├── etc/example_chain.rc     пример chain-automation
├── install.sh               one-liner установка
├── LICENSE (MIT) / README.md
```
