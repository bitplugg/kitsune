"""wireless/scan — мониторинг эфира в поисках AP (scapy, требует monitor mode)."""

import time

from kitsune import db
from kitsune.framework import Module

try:
    from scapy.all import Dot11Beacon, Dot11Elt, RadioTap, sniff

    HAVE_SCAPY = True
except ImportError:
    HAVE_SCAPY = False


class Module(Module):
    meta = {
        "name": "wireless/scan",
        "author": "kitsune",
        "description": "Passive AP scan via scapy (interface in monitor mode required)",
        "options": {
            "iface":   {"default": "wlan0mon", "required": True, "desc": "interface in monitor mode"},
            "seconds": {"default": "30", "required": False, "desc": "capture duration"},
        },
    }

    def run(self):
        if not HAVE_SCAPY:
            self.fail("scapy is not installed: pip3 install scapy")
            return
        aps = {}

        def handler(packet):
            if packet.haslayer(Dot11Beacon):
                ssid = packet[Dot11Elt].info.decode("utf-8", errors="replace").strip("\x00")
                bssid = packet[RadioTap].addr2
                signal = getattr(packet, "dBm_AntSig", "-")
                ch = packet[Dot11Elt].channel_info if hasattr(packet[Dot11Elt], "channel_info") else "?"
                prev = aps.get(bssid, {})
                aps[bssid] = {"ssid": ssid or "<hidden>", "ch": ch, "sig": signal}

        deadline = time.time() + float(self.seconds)
        self.status(f"sniffing {self.iface} for {self.seconds}s ... (Ctrl-C to stop)")
        try:
            while time.time() < deadline:
                sniff(iface=self.iface, prn=handler, count=200, timeout=5, store=False)
        except (KeyboardInterrupt, PermissionError) as e:
            self.warn(f"capture stopped: {e}")

        if not aps:
            self.warn("no APs captured")
            return
        for bssid, info in sorted(aps.items()):
            db.upsert_host(bssid, hostname=info["ssid"], source="wireless")
        self.ok(f"{len(aps)} AP(s) -> db")
        self.table(("BSSID", "SSID", "Channel", "Signal(dBm)"),
                   [(b, i["ssid"], str(i["ch"]), str(i["sig"])) for b, i in sorted(aps.items())])
