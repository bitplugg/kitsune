---
title: Framework — команды и CLI
---

# Framework — команды и CLI

## CLI-флаги (запуск из консоли ОС)

```bash
kitsune                        # интерактивный REPL
kitsune --version              # kitsune 0.1.0
kitsune -c 'use doctor; run'   # выполнить одну команду и выйти
kitsune -c 'use portscan; set target 10.0.0.1; set ports 1-1000; run; stats'
kitsune --resource etc/example_chain.rc   # выполнить chain-скрипт
```

Установка через `pipx install --editable /path/to/kitsune`.

## REPL-команды

### Модули
| Команда | Суть |
|---|---|
| `use <module>` | загрузить (`use portscan` = `use network/portscan`) |
| `info` | автор, описание, опции активного модуля |
| `show options` | таблица опций: значение, `required`, описание |
| `set <opt> <value>` | установить опцию |
| `run` | выполнить (нужны обязательные опции!) |
| `back` | выгрузить модуль |

### Данные (общая база)
| Команда | Суть |
|---|---|
| `show modules` | все 25 модулей + описания |
| `show hosts` / `show ports` | хосты и открытые порты из db |
| `show subdomains` | субдомены из db |
| `show sessions` | история шелл-сессий из db |
| `show loot` | все находки (web_path, cve, exfil, сессии...) |
| `show all` | всё сразу |
| `stats` | счётчики по таблицам + путь к db |

### Сессии (msf-стиль)
| Команда | Суть |
|---|---|
| `sessions` | список live-шеллов (`Idx`, `Host`, `LIVE`) + история из db |
| `interact <id>` | взять shell в руки (промпт `kitsune (shell) >`), `exit` — вернуться |

### Автоматизация
| Команда | Суть |
|---|---|
| `setvar <n> <v>` | переменная для подстановки: `setvar target 10.0.0.1` |
| `resource <file.rc>` | выполнить файл команд (REPL-скрипт); `${var}` подставляются |

Пример `etc/example_chain.rc`:

```
setvar target 127.0.0.1
use portscan
set target ${target}
set ports 8780-8810
run
back
use techdetect
set url http://${target}:8803/
run
report kitsune_chain_report.md
```

### Обслуживание
| Команда | Суть |
|---|---|
| `report [file]` | отчёт из db; `.md` или `.html` |
| `dashboard` | curses-TUI обзор (статистика, модули, loot), `q` — выход |
| `doctor` | окружение: python/scapy/ip/iw/nmap/hashcat/internet/db | 
| `resetdb [yes]` | очистка базы (требует `resetdb yes`) |
| `clear` / `?` / `exit` / `q` | соответственно |

## Пейперное правило

**Каждый модуль пишет в db** и каждый следующий модуль может использовать
результаты: `portscan` → `techdetect` → `dirfuzz` → `sqli` → `exfil`.

Дальше: [network](02-network.md) · [wireless/deauth](08-wireless.md)
