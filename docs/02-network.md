---
title: Network — portscan, discovery
---

# Network layer

## network/portscan

TCP-сканер на чистых сокетах (аналог `nmap -T4`). Результат в db → visible
для других модулей.

```bash
kисtsune > use portscan
kitsune (network/portscan) > show options
kitsune (network/portscan) > set target 192.168.1.0/24
kitsune (network/portscan) > set ports 1-1000    # 'top' | '80,443' | '1-1024'
kitsune (network/portscan) > set threads 200
kitsune (network/portscan) > run
```

**Опции:**
| Опция | required | Описание |
|---|---|---|
| `target` | yes | host или CIDR (`10.0.0.1`, `192.168.1.0/24`) |
| `ports` | no | `top` (31 порт) | диапазон | список |
| `threads` | no | concurrency (default 200) |
| `timeout` | no | seconds (1.5) |

**Что умеет дополнительно:** grab banner у характерных служб (ftp/ssh/smtp/mysql/redis...), определение сервиса по порту, лимит `MAX_HOSTS=4096` (защита от тупого `/0`).

## network/discovery

Быстрый TCP-свип подсети: смотрит common-порты и живых хостов в db:

```bash
kitsune > use discovery
kitsune (network/discovery) > set target 192.168.1.0/24
kitsune (network/discovery) > run
# → "N alive host(s)" в db
```

**Опции:** `target` (required), `ports` (22,80,443,445,3389,8080), `threads`, `timeout 0.8`.

Дальше: [recon](03-recon.md)
