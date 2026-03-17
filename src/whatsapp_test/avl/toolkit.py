import hashlib
import os
import subprocess
import time
from datetime import datetime

from whatsapp_test.whatsapp_adapter import WhatsAppAdapter

from .models import Observation


class AvlToolkit:
    def __init__(self, adapter: WhatsAppAdapter, out_dir: str, dry_run: bool) -> None:
        self.adapter = adapter
        self.out_dir = out_dir
        self.dry_run = dry_run
        os.makedirs(self.out_dir, exist_ok=True)

    def capture_screenshot(self, step: int) -> Observation:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = os.path.join(self.out_dir, f"step_{step:03d}_{ts}.png")
        if self.dry_run:
            with open(path, "wb") as f:
                f.write(b"dry-run")
        else:
            result = subprocess.run(
                ["screencapture", "-x", path],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                raise RuntimeError(f"Screenshot failed: {result.stderr.strip()}")
        digest = self._sha256(path)
        return Observation(step=step, screenshot_path=path, screenshot_sha256=digest)

    @staticmethod
    def _sha256(path: str) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            h.update(f.read())
        return h.hexdigest()

    def run_action(self, name: str, payload: dict) -> str:
        if self.dry_run:
            return f"[dry-run] {name} {payload}"

        if name == "activate_whatsapp":
            self.adapter.activate_whatsapp()
            return "activated"
        if name == "select_chat":
            self.adapter.select_chat(payload["contact"])
            return "chat-selected"
        if name == "paste_message":
            self.adapter.paste_message(payload["message"], send=False)
            return "message-pasted"
        if name == "send_message":
            # Send Enter only (message is already in composer)
            script = """
            tell application "System Events"
              key code 36
            end tell
            """
            result = self.adapter._run_osascript(script)  # noqa: SLF001
            if result.returncode != 0:
                raise RuntimeError(f"Send failed: {result.stderr.strip()}")
            return "message-sent"
        if name == "wait":
            time.sleep(float(payload.get("seconds", 0.2)))
            return "waited"
        if name == "done":
            return "done"
        raise RuntimeError(f"Unknown action: {name}")

