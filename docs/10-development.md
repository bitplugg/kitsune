---
title: Development — свой модуль за 60 строк
---

# Development / кастомные модули

## Как устроен модуль

Каждый модуль = файл в `kitsune/modules/<layer>/<name>.py` с классом `Module`:

```python
from kitsune import db
from kitsune.framework import Module

class Module(Module):
    meta = {
        "name": "network/portscan",           # layer/name — так warices регистрируются
        "author": "kitsune",
        "description": "Socket-based TCP port scanner...",
        "options": {
            "target":  {"default": "", "required": True, "desc": "host or CIDR"},
            "threads": {"default": "200", "required": False, "desc": "concurrency"},
        },
    }

    def run(self):
        self.status(f"target={self.target}")
        ...                                   # вся логика
        db.add_loot("my_category", self.target, "что нашли")
        self.ok("найдено N, записано в db")
        self.table(("Col A", "Col B"), [(1, 2), (3, 4)])
```

## Что есть в Module

| Метод | Суть |
|---|---|
| `self.ok / fail / warn / status / print` | цветной вывод `+/-/!/*` |
| `self.table(headers, rows)` | ASCII-таблица |
| `self.db()` / `from kitsune import db` | общая база |

## Хелперы db

```python
from kitsune import db
db.upsert_host("10.0.0.5", hostname="foo", source="my_module")
db.add_port("10.0.0.5", 22, service="ssh", banner="SSH-2.0")
db.add_subdomain("api.foo", "10.0.0.5")
db.add_loot("my", "10.0.0.5", "деталь находки")
db.stat()                      # {'hosts': n, ...}
db.add_session(host, port) / db.close_session(sid) / db.list_sessions()
```

**Правило:** всё, что нашёл, — пишем в db (loot/hosts/ports/subdomains).
Это позволяет report, dashboard, API и другим модулям автоматически
использовать ваши находки.

## Жизненный цикл модуля (скелет)

1. meta: name (layer/name), description, options (+ required)
2. `run()` = стартовая точка; **опции уже на self.target, self.threads** (тип строки)
3. аккуратно ловите `OSError / socket.timeout`
4. Вывод: статус-таблица + запись в db; не бросайте исключения наверх (фреймворк
   поймает, но лучше оборачивать)

## Регистрация

- Файл кладётся поверх под каталог `kitsune/modules/<layer>/`
- `__init__.py` пакета достаточно: `"""kitsune package marker."""`
- Framework autodiscovered при старте: `show modules` покажет вашему модулю имя.

## Индекс тестирования модуля

```bash
python3 -m unittest discover -s tests -v
python3 main.py -c "use '<new_name>'; info; run"
```

## Стиль-гайд

- Только stdlib в core; scapy и прочее — graceful degrade (см. `wireless/scan`)
- Вывод таблиц уже стинован (как в msf) — используйте self.table
- Пять каталогов layers: network, recon, web, exploits, payloads, post,
  wireless, api, team.
