"""Kitsune — общая база данных сессии.

Все модули пишут результаты сюда: hosts -> ports -> creds -> loot.
Это ядро "сквозной" идеи: 每个 модуль может использовать вывод другого.
"""

import os
import sqlite3
import threading

DB_DIR = os.path.expanduser("~/.kitsune")
DB_PATH = os.path.join(DB_DIR, "session.db")

_local = threading.local()

SCHEMA = """
CREATE TABLE IF NOT EXISTS hosts (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    host     TEXT UNIQUE NOT NULL,
    hostname TEXT,
    os_guess TEXT,
    alive    INTEGER DEFAULT 1,
    source   TEXT,
    added_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS ports (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    host_id  INTEGER NOT NULL REFERENCES hosts(id),
    port     INTEGER NOT NULL,
    proto    TEXT DEFAULT 'tcp',
    service  TEXT,
    banner   TEXT,
    UNIQUE(host_id, port, proto)
);

CREATE TABLE IF NOT EXISTS subdomains (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    host_id INTEGER REFERENCES hosts(id),
    name  TEXT UNIQUE NOT NULL,
    ip    TEXT,
    added_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS loot (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,          -- sqli | creds | vuln | ...
    target   TEXT,
    data     TEXT,
    added_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sessions (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    host      TEXT NOT NULL,
    port      INTEGER NOT NULL,
    status    TEXT DEFAULT 'open',
    opened_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS notes (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT,
    added_at TEXT DEFAULT (datetime('now'))
);
"""


def connect() -> sqlite3.Connection:
    """Получить соединение (по одному на поток, как принято в sqlite)."""
    conn = getattr(_local, "conn", None)
    if conn is None:
        os.makedirs(DB_DIR, exist_ok=True)
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA)
        _local.conn = conn
    return conn


def query(sql: str, params: tuple = ()) -> list:
    return connect().execute(sql, params).fetchall()


def execute(sql: str, params: tuple = ()) -> int:
    cur = connect().execute(sql, params)
    connect().commit()
    return cur.lastrowid


# --- удобные хелперы, которыми пользуются модули -------------------------

def upsert_host(host: str, hostname: str = "", source: str = "", os_guess: str = ""):
    execute(
        "INSERT INTO hosts (host, hostname, source, os_guess) VALUES (?,?,?,?) "
        "ON CONFLICT(host) DO UPDATE SET alive=1",
        (host, hostname, source, os_guess),
    )
    row = query("SELECT id FROM hosts WHERE host = ?", (host,))
    return row[0]["id"] if row else None


def add_port(host: str, port: int, service: str = "", banner: str = "", proto: str = "tcp"):
    host_id = upsert_host(host, source="portscan")
    execute(
        "INSERT INTO ports (host_id, port, proto, service, banner) VALUES (?,?,?,?,?) "
        "ON CONFLICT(host_id, port, proto) DO UPDATE SET service=excluded.service, banner=excluded.banner",
        (host_id, port, proto, service, banner),
    )


def add_subdomain(name: str, ip: str = ""):
    try:
        execute("INSERT INTO subdomains (name, ip) VALUES (?,?)", (name, ip))
        return True
    except sqlite3.IntegrityError:
        return False


def add_loot(category: str, target: str, data: str):
    execute("INSERT INTO loot (category, target, data) VALUES (?,?,?)", (category, target, data))


def add_session(host: str, port: int) -> int:
    return execute("INSERT INTO sessions (host, port) VALUES (?,?)", (host, port))


def close_session(session_id: int):
    execute("UPDATE sessions SET status='closed' WHERE id=?", (session_id,))


def list_sessions() -> list:
    return query("SELECT * FROM sessions ORDER BY id")


def stat() -> dict:
    counts = {}
    for table, label in [("hosts", "hosts"), ("ports", "ports"),
                         ("subdomains", "subdomains"), ("loot", "loot"),
                         ("sessions", "sessions")]:
        row = query(f"SELECT COUNT(*) AS c FROM {table}")
        counts[label] = row[0]["c"] if row else 0
    return counts
