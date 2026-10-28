---
title: Recon — subdomain, dnsenum, whois, crtsh
---

# Recon layer

## recon/subdomain

DNS-брутфорс субдоменов по встроенному словарю (~65 слов) или вашему:

```bash
kисtsune > use subdomain
kitsune (recon/subdomain) > set domain example.com
kitsune (recon/subdomain) > set wordlist /path/words.txt   # необязательно
kitsune (recon/subdomain) > run
```

Результат: живые субдомены → db (и хосты с `ip`). new ones подсвечиваются.

## recon/dnsenum

Resolve A/AAAA + угадывание типовых инфра-имён (`www, mail, ns1, api, vpn...`)
+ reverse-lookup PTR:

```bash
use dnsenum → set domain example.com → run
```

## recon/whois

Классический whois через **порт 43** (raw socket, без внешних команд):

```bash
use whois → set domain example.com → run
```

Выводит: registrar, creation/expiry dates, name servers; складывает в loot.

## recon/crtsh

Пассивно-пассивный сбор субдоменов через Certificate Transparency
crt.sh (JSON API). Не касаясь цели:

```bash
use crtsh → set domain example.com → run
# ищет сертификаты *.example.com → уникальные names → db
```

Аккуратно: crt.sh иногда медленно реагирует — лимит 15 сек по умолчанию.

Дальше: [web](04-web.md)
