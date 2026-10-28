---
title: Web — sqli, dirfuzz, xss, techdetect
---

# Web layer

## web/sqli

**Детектор** error-based SQL-инъекций (sqlmap-логика, stdlib HTTP):

```bash
kitsune > use sqli
kitsune (web/sqli) > set url http://site.com/item.php?id=1
kitsune (web/sqli) > set param id          # опционально: один параметр
kitsune (web/sqli) > run
```

Что происходит:
1. baseline запрос → сравнение body
2. каждый параметр бьётся пейлоадами `'`, `)`, `')`, `" , "1`, `\`
3. ищем сигнатуры ошибок MySQL/Postgres/MSSQL/Oracle/SQLite/generic
4. находки → loot (`sqli`). Заметка: только error-based, только детект.

## exploits/web/sqli_union

Подбор **union-колонок** и выdumpка `version()`/`user()` (переход к
эксплуатации):

```bash
use sqli_union
set url http://site.com/item.php?id=1
set param id
run     # → "union ... N columns!" + version() + user() в loot
```

Требует числового параметра; техника union + `CONCAT_WS(0x3f,0x4b37,...)`
маркер `K7?` ищется в ответе.

## web/dirfuzz

Брутфорс путей/файлов (dirb/gobuster логика; 61 встроенный вариант
`admin`, `robots.txt`, `.git/config`, `phpmyadmin/`...). Многопоточно.

```bash
use dirfuzz
set url http://site.com/
set threads 30
run         # hits: status 200/401/403 → loot(web_path)
```

## web/xss

Probe отражённых инъекций: маркерные пейлоды (`<script>`, `<img onerror>`,
`<svg onload>`) по каждому параметру; match в HTML → loot(`xss`).

```bash
use xss → set url http://site.com/?q=test → run
```

## web/techdetect

Fingerprint стека: заголовки `Server`, `X-Powered-By`, `X-AspNet-Version`,
`X-Generator`, title, hints по html (wp-content, django, laravel...). Результат
— bpут в db.

```bash
use techdetect → set url http://site.com/ → run
```

Дальше: [exploits](05-exploits.md)
