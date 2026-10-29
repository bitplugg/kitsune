"""wireless/scan — мониторинг эфира с канальным hopping'ом (scapy).

Требует iface в monitor mode (wireless/monitor start).
RTL8821CE и другие rtw88-карты обычно НЕ ловят что-либо на «статичном»
канале — поэтому есть режим hopping по 1..13 (airodump-mini).
"""

import subprocess
import time

from kitsune import db
from kitsune.framework import Module

try:
    from scapy.all import Dot11Beacon, Dot11Elt, RadioTap, sniff

    HAVE_SCAPY = True
except ImportError:
    HAVE_SCAPY = False

CHANNELS = list(range(1, 14))  # 2.4GHz 1..13


class Module(Module):
    meta = {
        "name": "wireless/scan",
        "author": "kitsune",
        "description": "Sniff APs with channel hopping (airodump-mini); iface must be in monitor mode",
        "options": {
            "iface":   {"default": "wlan0", "required": True, "desc": "interface in monitor mode"},
            "seconds": {"default": "30", "required": False, "desc": "capture duration"},
            "channel": {"default": "", "required": False, "desc": "single channel 1-13; empty = hop 1..13"},
            "hop_sec": {"default": "1", "required": False, "desc": "per-channel dwell (hop mode)"},
            "threads": {"default": "1", "required": False, "desc": "не используется; заглушка совместимости"},
        },
    }

    def run(self):
        if not HAVE_SCAPY:
            self.fail("scapy is not installed (pipx inject kitsune scapy)")
            return
        iface = self.iface.strip()
        state = {"ch": "?"}   # текущий канал — читается из prn-handler
        aps: dict[str, dict] = {}

        def handler(packet):
            if not packet.haslayer(Dot11Beacon):
                return
            try:
                ssid = packet[Dot11Elt].info.decode("utf-8", errors="replace").strip("\x00") or "?"
                bssid = packet[RadioTap].addr2 or "?"
                sig = getattr(packet, "dBm_AntSig", None) or "-"
                prev = aps.get(bssid, {})
                aps[bssid] = {
                    "ssid": ssid[:24],
                    "ch": state["ch"],
                    "sig": sig,
                    "count": prev.get("count", 0) + 1,
                }
            except Exception:
                pass

        total = float(self.seconds)
        end = time.time() + total
        ch_spec = self.channel.strip()
        hop_sec = float(self.hop_sec)
        self.warn(f"sniffing {iface} for {total}s (channel={ch_spec or f'hop 1..13/{hop_sec}s'}) "
                  f"(Ctrl-C to stop)")

        try:
            if ch_spec:
                self._set_channel(iface, int(ch_spec))
                state["ch"] = ch_spec
                while time.time() < end:
                    sniff(iface=iface, prn=handler, count=100, timeout=3, store=False)
            else:
                while time.time() < end:
                    for ch in CHANNELS:
                        if time.time() >= end:
                            break
                        state["ch"] = ch
                        self._set_channel(iface, ch)
                        sniff(iface=iface, prn=handler, count=50, timeout=hop_sec, store=False)
        except (KeyboardInterrupt, PermissionError) as e:
            self.warn(f"capture stopped: {e}")

        if not aps:
            self.warn("no APs captured")
            self.warn("проверки: iw dev %s info (type monitor?) · драйвер rtw88 спит на каналах ·"
                      " попробуйте channel=6 если ваш AP на нём" % iface)
            return

        for bssid, info in sorted(aps.items()):
            db.upsert_host(bssid, hostname=info["ssid"], source="wireless")
        self.ok(f"{len(aps)} AP(s) -> db")
        self.table(("BSSID", "SSID", "Channel", "Signal(dBm)", "Beacons"),
                   [(b, i["ssid"], str(i["ch"]), str(i["sig"]), str(i["count"]))
                    for b, i in sorted(aps.items(), key=lambda kv: -kv[1]["count"])])

    @staticmethod
    def _set_channel(iface: str, ch: int):
        subprocess.run(["iw", "dev", iface, "set", "channel", str(ch)],
                       check=False, capture_output=True, timeout=2)
