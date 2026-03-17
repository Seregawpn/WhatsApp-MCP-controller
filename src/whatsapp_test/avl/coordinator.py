from .models import Action, AvlGoal, AvlState
from .toolkit import AvlToolkit


class AvlCoordinator:
    def __init__(self, toolkit: AvlToolkit, analyzer: object) -> None:
        self.toolkit = toolkit
        self.analyzer = analyzer
        self.state = AvlState()

    def run(self, goal: AvlGoal) -> str:
        for step in range(1, goal.max_steps + 1):
            obs = self.toolkit.capture_screenshot(step=step)
            action: Action = self.analyzer.decide(goal=goal, state=self.state, obs=obs)
            self._apply_state_before(action)
            outcome = self.toolkit.run_action(action.name, action.payload)
            self._apply_state_after(action, outcome)
            if self.state.done:
                return (
                    f"AVL done at step {step}. "
                    f"Last action={action.name}, screenshot={obs.screenshot_path}"
                )
        raise RuntimeError(f"AVL exceeded max steps ({goal.max_steps})")

    def _apply_state_before(self, action: Action) -> None:
        if action.name == "done":
            self.state.done = True

    def _apply_state_after(self, action: Action, _outcome: str) -> None:
        if action.name == "activate_whatsapp":
            self.state.activated = True
            return
        if action.name == "select_chat":
            self.state.chat_selected = True
            return
        if action.name == "paste_message":
            self.state.message_pasted = True
            return
        if action.name == "send_message":
            self.state.sent = True
            self.state.done = True
            return
        if action.name == "done":
            self.state.done = True
