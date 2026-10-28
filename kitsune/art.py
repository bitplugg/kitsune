"""Kitsune art — баннер в стиле msfconsole: ASCII + =[ brackets ] + случайный tip."""

import random

RESET = "\033[0m"
DIM = "\033[2m"
BOLD = "\033[1m"
COLORS = [
    "\033[38;5;208m",  # orange
    "\033[31m",        # red
    "\033[33m",        # yellow
    "\033[35m",        # magenta
    "\033[36m",        # cyan
]

VERSION = "0.1.0"
CODENAME = "Nebula"

ARTS = [
    # 1. fox face
    r"""
   /\___/\
  ( o  o )  /——————————\
  /  ^  \  (  kitsune  )
  \  -  /  /  v0.1.0   \
  /     \  \  "Nebula" /
 /  | |  \ /——————————\
""",
    # 2. nine tails
    r"""
      /\/\   /\/\/   /\/\
     /    \ /    \ /    \
   ◢◤  九   尾   ◢◤  v0.1.0
 nine tails · one framework
""",
    # 3. kitsune mask
    r"""
      \WWWWWW/
     _/      \_
     |  ▲  ▲  |
     \    V   /
      \  Σ  /
       \  /    ~ kitsune
        \/
""",
    # 4. running fox
    r"""
                 ,
        ___.    /
      .'   "-./ |
     /  /\    \  \___
     |  \/    '.___. \
      \        \    \ |
       \_______ \    |__/
               \/__________\/
""",
    # 5. block letters
    r"""
  ▄▄▄▄  ▄   ▄ ▄   ▄  ▄▄  ▄▄▄  ▄  ▄
   ▄▄▀ ▐▌  ▌ ▐   ▌   ▌  ▐▌  ▐▌  ▌
   ▐  ▌ ▚▄▄▌  ▚ ▞  ▐▌  ▐▌  ▐▌  ▌
   ▀▀▀          ▀
""",
]

TIPS = [
    "use `tab` для автодополнения модулей и опций",
    "sessions → interact <id> — взять подсоединённый shell в руки",
    "resource etc/example_chain.rc — полная авто-цепочка разведки",
    "помни: сначала `set target`, потом `run` — не наоборот",
    "show all — быстрый взгляд на всё, что нарыли",
    "doctor подскажет, чего не хватает окружению",
    "ловушки чужих пакетов: python3 -m pip list | grep scapy",
    "wireless/scan требует monitor mode — сначала wireless/monitor start",
    "report audit.html выглядит лучше в браузере чем в терминале",
    "не забудь payload/listener ДО запуска жертвы — иначе кто слушать будет?",
    "loot автоматически копится в db — общий тактический склад",
    "результаты portscan видят другие модули — цепляй в цепь через resource",
    "в девятихвостые поступают по дрековости: сначала recon, потом exploits",
    "усыпление: deauth работает с broadcast MAC — все отваливаются разом",
    "have fun, но только на вашем лабораторном стенде",
    "запрещено использовать против систем без разрешения!",
    "модуль api/serve удобно вешать на 127.0.0.1 — не свети наружу",
    "cve_search → NVD API — без ключа; не злоупотребляй rate limits",
    "kадры прячут proxy в ~/.kitsune/session.db тоже — чищи resetdb yes",
    "учунуться в модуль? открой kitsune/modules/<имя>.py — весь фреймворк питон",
]

_BANNER_W = 52


def _bracket(text: str) -> str:
    text = text.rstrip()
    if len(text) < _BANNER_W:
        text += " " * (_BANNER_W - len(text))
    return "[" + text + "]"


def _module_counts(modules) -> list:
    """Разбить модули по группам: [('scan', 3), ('recon', 4), ...]"""
    labels = {
        "network": "scan",
        "recon": "recon",
        "web": "web",
        "exploits": "exploits",
        "payloads": "payloads",
        "post": "post",
        "wireless": "wireless",
        "api": "api",
        "team": "team",
    }
    counts = {}
    for name in modules:
        prefix = name.split("/", 1)[0]
        counts[prefix] = counts.get(prefix, 0) + 1
    return [(label, counts[key]) for key, label in labels.items() if key in counts]


def random_banner(modules=None) -> str:
    art = random.choice(ARTS)
    color = random.choice(COLORS)
    tip = random.choice(TIPS)

    # первая строка `=[ ... ]`
    head = f' kitsune v{VERSION} "{CODENAME}" · nine-tails intact '
    out = [color + art + RESET]
    out.append(BOLD + "       =" + _bracket(head) + RESET)

    # счётчики модулей по 3-4 группы на строку
    if modules:
        parts = _module_counts(modules)
        chunks = [parts[i:i + 4] for i in range(0, len(parts), 4)]
        for chunk in chunks:
            text = f"{len(modules)} modules - " if chunk is chunks[0] else ""
            text += " - ".join(f"{c} {l}" for l, c in chunk)
            if chunk is chunks[-1]:
                text += " - 0 evasion"
            out.append(DIM + "+ -- --=" + RESET + BOLD + _bracket(text) + RESET)

    out.append(DIM + "     Tip: " + tip + RESET)
    out.append(DIM + "     https://github.com/kitsune-fw/kitsune (fictional)" + RESET)
    return "\n".join(out) + "\n" + RESET

# совместимость со старыми вызовами (tui, dashboard)
TAGLINES = TIPS
