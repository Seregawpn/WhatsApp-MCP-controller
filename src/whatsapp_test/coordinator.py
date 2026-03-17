import platform

from .models import RunRequest
from .permission_gate import PermissionState, PermissionGate
from .whatsapp_adapter import WhatsAppAdapter


class InteractionCoordinator:
    """Single source of truth for run decisions."""

    def __init__(self, gate: PermissionGate, adapter: WhatsAppAdapter) -> None:
        self.gate = gate
        self.adapter = adapter

    def execute(self, req: RunRequest) -> str:
        if platform.system() != "Darwin":
            raise RuntimeError("This mini-project currently supports macOS only.")
        if not req.message.strip():
            raise RuntimeError("Message is empty.")

        permission: PermissionState = self.gate.check()
        if not permission.accessibility_ok:
            raise RuntimeError(permission.details)

        if req.dry_run:
            return "Dry-run OK: permission passed, WhatsApp action skipped."

        self.adapter.activate_whatsapp()
        if req.contact and req.contact.strip():
            self.adapter.select_chat(req.contact.strip())
        self.adapter.paste_message(req.message, send=req.send)
        return "Success: message pasted" + (" and sent." if req.send else ".")
