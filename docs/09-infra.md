---
title: Infra — REST API, team sync, отчёты, TUI
---

# Infra layer

## api/serve (msfrpcd-lite)

REST API поверх общей базы на stdlib `http.server`:

```bash
kitsune > use serve
kitsune (api/serve) > set port 8000
kitsune (api/serve) > set host 127.0.0.1      # не светите на 0.0.0.0!
kitsune (api/serve) > set seconds 60          # uptime
kitsune (api/serve) > run
```

| Endpoint | Что уходит |
|---|---|
| `/api/hosts` | hosts + hostname |
| `/api/ports` | host, port, service, banner |
| `/api/subdomains` | все субдомены |
| `/api/loot` | все находки |
| `/api/sessions` | сессии читателей чела |
| `/api/stats` | счётчики таблиц |
| `/api/report` | ready markdown (как `report`) |

```bash
curl http://127.0.0.1:8000/api/stats
curl http://127.0.0.1:8000/api/loot | jq .
```

Клиенты: собственный GUI, скрипты автоматизации, bot Telegram.

## team/sync (мульти-оператор)

Один оператор держит hub **mode=serve**, остальные свои loot **push** им.

```bash
# оператор 1 (сервер):
use team/sync → set mode serve → set port 9901 → set seconds 120 → run

# оператор 2 (отправить находки):
use team/sync → set mode push → set port 9901 → set remote <ip_hub> → run
```

Как работает: HTTP POST `/merge`, JSON с hosts/ports/loot;
svтя серверных данных mass-insert (~INSERT OR IGNORE, дубликатов нет);
в конце printering сколько нового получено. Оба оператора ходят
в одну db — либо их hub, либо копии.

## Отчёты

| Команда | Что дает |
|---|---|
| `report x.md` | markdown: summary, hosts, ports, subdomains, sessions, loot |
| `report x.html` | тёмная тема, CSS, красиво для браузера/цресс (Ctrl+P → PDF) |

Оба рендера из одного `kitsune/report_md.py` — CLI в REPL и
`/api/report` у API используют один код.

## dashboard (TUI)

```
kitsune > dashboard
```

curses-обзор: счётчики, группы модулей, host имен `LOOT (last)`;
`q` — выход.

## С ETF-конфигом инстанces

```
# once: создать центральный itl
kitsune --resource etc/example_chain.rc       # cjekы полного пентеста
```

Каждое свойство stupni добавляет в db — потом `report` и `dashboard` показывают.
