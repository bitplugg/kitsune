---
title: Overview — архитектура и жизненный цикл
---

# Overview

## Что такое kitsune

`kitsune` — nine-tailed pentest framework: единый CLI, объединяющий подходы
nmap / metasploit / aircrack-ng / routersploit / sqlmap. Один бинарь (pipx / venv),
25 модулей, **нулевые обязательные зависимости** (ядро — stdlib: `socket`, `sqlite3`,
`curses`, `http.server`).

## Ключевая идея: общая база сессии

Всё, что находит любой модуль, кладётся в одну базу
`~/.kitsune/session.db` (SQLite):

```
hosts → ports → subdomains → loot(находки) → sessions(шеллы)
```

Именно ради этогоkitsune существует: `portscan` обнаружил 80 порт →
`techdetect` по URL уже знает хост; `display listener` поймал шелл →
`post/enum` снимает intel → всё визуализируется `report`/`dashboard`.
Данные текут **между модулями без ручной прокидки**.

## Архитектура

```
kitsune/
├── main.py          # вход (CLI: REPL / -c / --resource)
├── kitsune/
│   ├── cli.py       # argparse → console
│   ├── console.py   # REPL + batch dispatch
│   ├── framework.py # реестр модулей, команды, таблицы
│   ├── db.py        # общая SQLite (hosts/ports/loot/sessions)
│   ├── report_md.py # рендеры отчёта (markdown + html)
│   ├── tui.py       # curses dashboard
│   ├── art.py       # случайные баннеры в стиле msfconsole
│   └── modules/
│       ├── network/ recon/ web/ exploits/
│       ├── payloads/ post/ wireless/
│       └── api/ team/
```

## Командная модель

Все 9 направлений — модули с одинаковым интерфейсом:

```
kадры > use <module>      # загрузить (короткое имя ок: use portscan)
kitsune (layer/name) > info
kitsune (layer/name) > show options
kitsune (layer/name) > set <option> <value>
kitsune (layer/name) > run        # блокирует REPL до конца
kitsune (layer/name) > back
```

Вывод модуля — цветные строки `[*]/[+]/[-]/[!]` + ASCII-таблицы.

## Lifecycle атаки

```
1 Recon:      discovery · subdomain · dnsenum · whois · crtsh · techdetect
2 Probing:    portscan (tcp 1-...)  → что открыто, что за службы
3 Web:        dirfuzz · xss · sqli · sqli_union · path_traversal
4 Exploits:   shellshock · auth_bypass(роутеры) · cve_search
5 Payloads:   listener (ловим шеллы) → sessions → interact
6 Post:       enum (id/uname/окружение) · exfil (файлы)
7 Wireless:   monitor → scan → deauth → (handshake ловится инструментов)
8 Reporting:  report audit.md|html · dashboard · api/serve · team/sync
9 Cleanup:    resetdb yes
```

## Что читаем дальше

- [Framework commands](01-framework.md) — команды REPL и CLI-флаги
- [Wireless](08-wireless.md) — подробный раздел (monitor/scan/**deauth**)
- [Development](10-development.md) — свой модуль за 60 строк
