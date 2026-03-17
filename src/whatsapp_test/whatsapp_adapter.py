import subprocess
import time


class WhatsAppAdapter:
    """System input adapter for WhatsApp Desktop via AppleScript."""

    @staticmethod
    def _run_osascript(script: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            check=False,
        )

    @staticmethod
    def _copy_to_clipboard(text: str) -> None:
        subprocess.run(["pbcopy"], input=text, text=True, check=True)

    def activate_whatsapp(self) -> None:
        script = 'tell application "WhatsApp" to activate'
        result = self._run_osascript(script)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to activate WhatsApp: {result.stderr.strip()}")
        time.sleep(0.35)

    def select_chat(self, contact: str) -> None:
        self._copy_to_clipboard(contact)
        select_script = """
        tell application "System Events"
          -- Prefer chat switcher search first.
          keystroke "k" using command down
          delay 0.25
          keystroke "v" using command down
          delay 0.65
          -- Move to first result and open it.
          key code 125
          delay 0.08
          key code 36
          delay 0.15
          -- Close any leftover search UI.
          key code 53
        end tell
        """
        select_result = self._run_osascript(select_script)
        if select_result.returncode != 0:
            # Fallback to Cmd+F flow for older WhatsApp versions.
            fallback_select_script = """
            tell application "System Events"
              keystroke "f" using command down
              delay 0.25
              keystroke "v" using command down
              delay 0.65
              key code 125
              delay 0.08
              key code 36
              delay 0.15
              key code 53
            end tell
            """
            fallback_result = self._run_osascript(fallback_select_script)
            if fallback_result.returncode != 0:
                raise RuntimeError(
                    "Failed to select chat: "
                    f"{select_result.stderr.strip()} | fallback: {fallback_result.stderr.strip()}"
                )
        time.sleep(0.55)

    def focus_message_input(self) -> None:
        # Strategy A: focus last text area in front window.
        focus_script_a = """
        tell application "System Events"
          tell process "WhatsApp"
            set frontmost to true
            set taList to (every text area of front window)
            if (count of taList) is 0 then
              error "No text areas in front WhatsApp window"
            end if
            set targetArea to item -1 of taList
            set focused of targetArea to true
          end tell
        end tell
        """
        result_a = self._run_osascript(focus_script_a)
        if result_a.returncode == 0:
            time.sleep(0.12)
            return

        # Strategy B: close search and move focus with keyboard to composer.
        focus_script_b = """
        tell application "System Events"
          key code 53
          delay 0.08
          key code 48
          delay 0.08
          key code 48
          delay 0.08
          key code 48
          delay 0.08
          key code 48
        end tell
        """
        result_b = self._run_osascript(focus_script_b)
        if result_b.returncode == 0:
            time.sleep(0.12)
            return

        raise RuntimeError(
            "Failed to focus message input: "
            f"A={result_a.stderr.strip()} | B={result_b.stderr.strip()}"
        )

    def paste_message(self, text: str, send: bool) -> None:
        self.focus_message_input()
        self._copy_to_clipboard(text)
        paste_script = """
        tell application "System Events"
          keystroke "v" using command down
        end tell
        """
        paste_result = self._run_osascript(paste_script)
        if paste_result.returncode != 0:
            raise RuntimeError(f"Failed to paste message: {paste_result.stderr.strip()}")

        if send:
            send_script = """
            tell application "System Events"
              key code 36
            end tell
            """
            send_result = self._run_osascript(send_script)
            if send_result.returncode != 0:
                raise RuntimeError(f"Failed to send message: {send_result.stderr.strip()}")
