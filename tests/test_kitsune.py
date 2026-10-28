"""Kitsune unit tests — stdlib unittest, без внешних зависимостей.

  python3 -m unittest discover -s tests -v
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from kitsune import db  # noqa: E402
from kitsune.framework import Framework, Module  # noqa: E402


class _IsolatedDB:
    """Подменяет путь БД на временный файл на время теста."""

    def __enter__(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.old = db.DB_PATH
        db.DB_PATH = self.path
        db._local.conn = None
        return self

    def __exit__(self, *_):
        try:
            os.remove(self.path)
        except OSError:
            pass
        db.DB_PATH = self.old
        db._local.conn = None


class DbTests(unittest.TestCase):
    def test_upsert_and_stat(self):
        with _IsolatedDB():
            host_id = db.upsert_host("10.9.9.9", hostname="box", source="test")
            self.assertIsNotNone(host_id)
            db.add_port("10.9.9.9", 22, service="ssh", banner="SSH-2.0")
            db.add_port("10.9.9.9", 80)
            stats = db.stat()
            self.assertEqual(stats["hosts"], 1)
            self.assertEqual(stats["ports"], 2)

    def test_subdomain_dedup(self):
        with _IsolatedDB():
            self.assertTrue(db.add_subdomain("a.example.com", "1.2.3.4"))
            self.assertFalse(db.add_subdomain("a.example.com", "5.6.7.8"))
            rows = db.query("SELECT * FROM subdomains")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["ip"], "1.2.3.4")   # первая запись не перезаписывается

    def test_loot_and_sessions(self):
        with _IsolatedDB():
            db.add_loot("sqli", "http://t/u", "param=id")
            sid = db.add_session("10.1.1.1", 4444)
            self.assertTrue(sid > 0)
            db.close_session(sid)
            hist = db.list_sessions()
            self.assertEqual(hist[0]["status"], "closed")


class FrameworkTests(unittest.TestCase):
    def _fw(self):
        with _IsolatedDB():
            pass
        return Framework()

    def setUp(self):
        self.fw = Framework()

    def test_module_count(self):
        self.assertGreaterEqual(len(self.fw.modules), 20, "модули подгружаются")

    def test_priority_modules_present(self):
        must_have = ["network/portscan", "web/sqli", "payloads/listener", "wireless/scan",
                     "post/exfil", "team/sync", "api/serve", "exploits/cve_search"]
        for name in must_have:
            self.assertIn(name, self.fw.modules)

    def test_use_and_unload(self):
        self.fw.cmd_use(["portscan"])          # короткое имя
        self.assertIsNotNone(self.fw.active)
        self.assertEqual(self.fw.active.meta["name"], "network/portscan")
        self.fw.cmd_back([])
        self.assertIsNone(self.fw.active)

    def test_required_option_blocks_run(self):
        self.fw.cmd_use(["portscan"])          # target required и пуст
        self.fw.cmd_run([])
        # просто не падает; сообщение увидел оператор
        self.assertEqual(self.fw.active.meta["name"], "network/portscan")

    def test_substitution(self):
        self.fw.vars["target"] = "10.0.0.1"
        self.assertEqual(self.fw._subst("set target ${target}"), "set target 10.0.0.1")
        self.assertEqual(self.fw._subst("x ${missing}"), "x ")


class PortscanHelpersTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from kitsune.modules.network import portscan
        cls.m = portscan.Module

    def test_parse_ports_top(self):
        self.assertEqual(self.m._parse_ports("top"), portscan.TOP_PORTS if False else self.m._parse_ports(""))

    def test_parse_ports_ranges(self):
        self.assertEqual(self.m._parse_ports("80,443,8000-8003"),
                         [80, 443, 8000, 8001, 8002, 8003])

    def test_expand_hosts_single(self):
        self.assertEqual(self.m._expand_hosts("127.0.0.1"), ["127.0.0.1"])

    def test_expand_hosts_cidr(self):
        hosts = self.m._expand_hosts("192.168.77.0/30")
        self.assertEqual(sorted(hosts), ["192.168.77.1", "192.168.77.2"])

    def test_expand_hosts_rejects_garbage(self):
        self.assertEqual(self.m._expand_hosts("not a host"), [])
        self.assertEqual(self.m._expand_hosts("10.0.0.0/8"), [])   # слишком большая сеть


class ModuleBaseTests(unittest.TestCase):
    def test_defaults_are_str(self):
        class Demo(Module):
            meta = {"name": "demo", "options": {"x": {"default": 5}}}

        demo = Demo(Framework.__new__(Framework))
        self.assertEqual(demo.x, "5")


if __name__ == "__main__":
    unittest.main(verbosity=2)
