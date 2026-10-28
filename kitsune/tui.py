"""kitsune/tui — curses-дашборд: статистика, модули, активность, loot."""

import curses

from . import db


def draw(stdscr, modules: dict, stats: dict, loot_rows: list, tagline: str, host_rows: list):
    stdscr.erase()
    H, W = stdscr.getmaxyx()
    curses.curs_set(0)

    orange = curses.color_pair(1)
    green = curses.color_pair(2)
    yellow = curses.color_pair(3)
    dim = curses.color_pair(4)
    boldd = curses.color_pair(5)

    cols_w = min(60, max(30, W // 2))

    # левая колонка: статистика + сессии
    left = [
        ("KITSUNE v0.1.0 terminal", orange),
        (f" {tagline}", dim),
    ]
    for y, (txt, pair) in enumerate(left, 0):
        stdscr.addnstr(y, 0, txt, cols_w, pair)

    y_para = 3
    rows = [(k, str(v)) for k, v in stats.items()]
    try:
        height_hi = min(len(rows), H - 10)
        for i, (k, v) in enumerate(rows[:height_hi]):
            stdscr.addnstr(y_para + i, 0, f" {k:<12}", cols_w, dim)
            stdscr.addnstr(y_para + i, cols_w - 12, v, min(W, cols_w) - 12, green)
        # хосты
        y = y_para + height_hi + 1
        stdscr.addnstr(y, 0, "HOSTS (last 4)", cols_w, yellow)
        for i, h in enumerate(host_rows[:4]):
            y += 1
            stdscr.addnstr(y, 0, f" {h}", cols_w - 1, green)
    except (curses.error,):
        pass

    # правая колонка: модули
    try:
        mods = sorted(modules)
        start_x = cols_w + 2
        width = W - start_x - 1
        if width > 10:
            stdscr.addnstr(0, start_x, f"MODULES ({len(mods)})", width, orange)
            sys_cols = ["network", "recon", "web", "exploits", "payloads", "post",
                        "wireless", "api", "team"]
            for i, group in enumerate(sys_cols):
                hits = [m for m in mods if m.startswith(f"{group}/")]
                group_y = i * 3 + 2
                if group_y >= H - 2:
                    break
                stdscr.addnstr(group_y, start_x, f" {group}/", width, yellow)
                stdscr.addnstr(group_y, start_x + 10, "; ".join(
                    m.split('/', 1)[1] for m in hits[:3])[:max(0, width - 10)], width, dim)
    except (curses.error,):
        pass

    # нижняя панель: loot
    try:
        loot_y = max(10, H - min(len(loot_rows), 8) - 3)
        stdscr.addnstr(loot_y, 0, "LOOT (last)", W - 2, yellow)
        for i, item in enumerate(loot_rows[-7:]):
            y = loot_y + 1 + i
            txt = f" [{item['category']}] {item['target']} — {str(item['data'])[:40]}"
            stdscr.addnstr(y, 0, txt, W - 1, dim)
        stdscr.addnstr(H - 1, 0, " q: exit", min(W, 30), boldd)
    except (curses.error,):
        pass

    stdscr.refresh()


def main_loop(stdscr, modules, tagline):
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)

    last_host = [dict(r)["host"] for r in db.query("SELECT host FROM hosts ORDER BY id DESC LIMIT 4")]

    while True:
        stats = db.stat()
        loot = [dict(r) for r in db.query("SELECT * FROM loot ORDER BY id DESC LIMIT 8")]
        hosts = [dict(r)["host"] for r in db.query("SELECT host FROM hosts ORDER BY id DESC LIMIT 4")]
        draw(stdscr, modules, stats, loot, tagline, hosts)
        stdscr.nodelay(False)
        key = stdscr.getch()
        if key in (ord('q'), ord('Q'), 27):
            break
