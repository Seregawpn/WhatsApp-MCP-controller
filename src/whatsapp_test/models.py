from dataclasses import dataclass


@dataclass(frozen=True)
class PermissionState:
    accessibility_ok: bool
    details: str


@dataclass(frozen=True)
class RunRequest:
    contact: str | None
    message: str
    send: bool
    dry_run: bool
