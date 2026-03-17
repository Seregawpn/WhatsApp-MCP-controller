import base64
import json
import os
import re
import urllib.error
import urllib.request

from .models import Action, AvlGoal, AvlState, Observation

ALLOWED_ACTIONS = {
    "activate_whatsapp",
    "select_chat",
    "paste_message",
    "send_message",
    "wait",
    "done",
}


class DeterministicAnalyzer:
    def decide(self, goal: AvlGoal, state: AvlState, _obs: Observation) -> Action:
        if state.done:
            return Action(name="done", payload={})
        if not state.activated:
            return Action(name="activate_whatsapp", payload={})
        if not state.chat_selected:
            return Action(name="select_chat", payload={"contact": goal.contact})
        if not state.message_pasted:
            return Action(name="paste_message", payload={"message": goal.message})
        if goal.auto_send and not state.sent:
            return Action(name="send_message", payload={})
        return Action(name="done", payload={})


class LlmAnalyzer:
    """
    LLM-based analyzer for screenshot-driven loop.
    Falls back to deterministic policy on API or parse errors.
    """

    def __init__(self, model: str, api_key: str | None, fallback: DeterministicAnalyzer) -> None:
        self.model = model
        self.api_key = api_key
        self.fallback = fallback

    def decide(self, goal: AvlGoal, state: AvlState, obs: Observation) -> Action:
        if not self.api_key:
            return self.fallback.decide(goal, state, obs)
        try:
            return self._decide_via_api(goal, state, obs)
        except Exception:
            return self.fallback.decide(goal, state, obs)

    def _decide_via_api(self, goal: AvlGoal, state: AvlState, obs: Observation) -> Action:
        with open(obs.screenshot_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")

        system_prompt = (
            "You are an action planner for WhatsApp UI automation. "
            "Return ONLY JSON: {\"action\": <string>, \"payload\": <object>} "
            "with one action from: activate_whatsapp, select_chat, paste_message, send_message, wait, done."
        )
        user_context = {
            "goal": {
                "contact": goal.contact,
                "message": goal.message,
                "auto_send": goal.auto_send,
            },
            "state": {
                "activated": state.activated,
                "chat_selected": state.chat_selected,
                "message_pasted": state.message_pasted,
                "sent": state.sent,
                "done": state.done,
            },
            "observation": {
                "step": obs.step,
                "screenshot_sha256": obs.screenshot_sha256,
            },
            "required_policy": [
                "If whatsapp is not active: activate_whatsapp",
                "If target chat not selected: select_chat",
                "If chat selected and message not pasted: paste_message",
                "If auto_send true and message pasted and not sent: send_message",
                "Else: done",
            ],
        }
        body = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "generationConfig": {"temperature": 0.0},
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": json.dumps(user_context, ensure_ascii=True)},
                        {"inline_data": {"mime_type": "image/png", "data": b64}},
                    ],
                }
            ],
        }
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            raise RuntimeError(e.read().decode("utf-8")) from e

        data = json.loads(raw)
        text = self._extract_text(data).strip()
        if not text:
            raise RuntimeError("Empty model text")
        parsed = self._parse_json_from_text(text)
        action = parsed.get("action")
        payload = parsed.get("payload", {})

        if action not in ALLOWED_ACTIONS:
            raise RuntimeError(f"Unsupported action from model: {action}")
        if not isinstance(payload, dict):
            raise RuntimeError("Payload must be an object")

        if action == "select_chat":
            payload.setdefault("contact", goal.contact)
        if action == "paste_message":
            payload.setdefault("message", goal.message)
        if action == "wait":
            payload.setdefault("seconds", 0.25)

        return Action(name=action, payload=payload)

    @staticmethod
    def _extract_text(data: dict) -> str:
        candidates = data.get("candidates", [])
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        texts = [p.get("text", "") for p in parts if isinstance(p, dict)]
        return "\n".join(t for t in texts if t)

    @staticmethod
    def _parse_json_from_text(text: str) -> dict:
        stripped = text.strip()
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass

        # Support fenced blocks like ```json ... ```
        fenced = re.findall(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", stripped, flags=re.IGNORECASE)
        for block in fenced:
            try:
                return json.loads(block)
            except json.JSONDecodeError:
                continue

        # Last resort: first JSON object-like slice
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start >= 0 and end > start:
            return json.loads(stripped[start : end + 1])
        raise RuntimeError("Model output is not valid JSON")


def build_analyzer(
    model: str,
    force_deterministic: bool = False,
    api_key: str | None = None,
) -> object:
    fallback = DeterministicAnalyzer()
    if force_deterministic:
        return fallback
    if api_key is None:
        api_key = os.environ.get("GEMINI_API_KEY")
    return LlmAnalyzer(model=model, api_key=api_key, fallback=fallback)
