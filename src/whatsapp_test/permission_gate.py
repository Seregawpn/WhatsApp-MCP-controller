import subprocess

from .models import PermissionState


class PermissionGate:
    """Checks whether automation via System Events is likely available."""

    @staticmethod
    def _run_osascript(script: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            check=False,
        )

    def check(self) -> PermissionState:
        probe = 'tell application "System Events" to get name of first process'
        result = self._run_osascript(probe)
        if result.returncode == 0:
            return PermissionState(
                accessibility_ok=True,
                details="Accessibility automation is available.",
            )

        stderr = (result.stderr or "").strip()
        if not stderr:
            stderr = "System Events probe failed."

        return PermissionState(
            accessibility_ok=False,
            details=(
                f"{stderr} Enable Accessibility for Terminal/Codex in "
                "System Settings -> Privacy & Security -> Accessibility."
            ),
        )

