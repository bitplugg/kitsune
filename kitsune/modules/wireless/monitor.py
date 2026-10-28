"""wireless/monitor — поднять/снять monitor mode на интерфейсе (ip + iw)."""

import shutil
import subprocess

from kitsune import db
from kitsune.framework import Module


class Module(Module):
    meta = {
        "name": "wireless/monitor",
        "author": "kitsune",
        "description": "Put a wifi iface into monitor mode (or back to managed) via ip+iw",
        "options": {
            "iface":  {"default": "wlan0", "required": True, "desc": "wireless interface"},
            "action": {"default": "start", "required": False, "desc": "start (monitor) | stop (managed)"},
        },
    }

    def run(self):
        missing = [t for t in ("ip", "iw") if shutil.which(t) is None]
        if missing:
            self.fail(f"missing tools: {', '.join(missing)} (install iproute2 / iw)")
            return
        action = self.action.lower()
        mode = "monitor" if action == "start" else "managed"
        steps = [
            f"ip link set dev {self.iface} down",
            f"iw dev {self.iface} set type {mode}",
            f"ip link set dev {self.iface} up",
        ]
        self.status(f"{action}ing monitor mode on {self.iface} ...")
        for step in steps:
            try:
                proc = subprocess.run(step.split(), check=True,
                                      capture_output=True, text=True)
            except (subprocess.CalledProcessError, OSError) as e:
                detail = getattr(e, "stderr", "") or str(e)
                self.fail(f"`{' '.join(step)} — failed: {detail.strip()[:120]}`")
                self.warn("hint: sudo + rfkill unblock wifi + iface should be idle")
                return
        db.add_loot("action", self.iface, f"monitor mode {mode} via wireless/monitor")
        self.ok(f"iface {self.iface} is now in {mode} mode — pair with `wireless/scan`")
