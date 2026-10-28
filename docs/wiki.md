---
title: Kitsune Wiki — оглавление
---

# 🦊 Kitsune Wiki

Полнчики, документация по всем 25 модулям, командам и lifecycle'у атаки.
Быстрый возврат: [ландінг](https://bitplugg.github.io/kitsune/) · [github](https://github.com/bitplugg/kitsune)

## Основы

| Статья | О чём |
|---|---|
| [Overview](00-overview.md) | архитектура, общая SQLite-сессия, lifecycle атаки |
| [Framework commands](01-framework.md) | все REPL-команды + CLI-флаги (`-c`, `--resource`) |
| [Своя разработка (development)](10-development.md) | как написать свой модуль: `Module`, `meta`, `options`, `run` |

## Модули по слоям

| Слой | Модули | Статья |
|---|---|---|
| network | `portscan`, `discovery` | [02-network.md](02-network.md) |
| recon | `subdomain`, `dnsenum`, `whois`, `crtsh` | [03-recon.md](03-recon.md) |
| web | `sqli`, `dirfuzz`, `xss`, `techdetect` | [04-web.md](04-web.md) |
| exploits | `sqli_union`, `shellshock`, `path_traversal`, `auth_bypass`, `cve_search` | [05-exploits.md](05-exploits.md) |
| payloads | `reverse_shell`, `bind_shell`, `listener` | [06-payloads.md](06-payloads.md) |
| post | `enum`, `exfil` | [07-post.md](07-post.md) |
| wireless | `monitor`, `scan`, `deauth` | [08-wireless.md](08-wireless.md) |
| infra | `api/serve`, `team/sync` | [09-infra.md](09-infra.md) |

## Жизненный цикл атаки (полный цикл)

```
discovery → portscan → techdetect → dirfuzz/sqli/xss
    → exploits → listener → interact (живая сессия)
    → post/enum → post/exfil → report
```

Каждый шаг капает в общую БД — следующие модули используют наработки предыдущих.

## Правовая оговорка

**:warning: Используйте только на системах с явным разрешением** (CTF, ваш стенд, договорной пентест). За несанкционированные атаки отвечает оператор.
