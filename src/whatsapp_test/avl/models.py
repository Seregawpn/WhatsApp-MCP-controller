from dataclasses import dataclass


@dataclass(frozen=True)
class AvlGoal:
    contact: str
    message: str
    auto_send: bool
    max_steps: int
    out_dir: str
    dry_run: bool


@dataclass(frozen=True)
class Observation:
    step: int
    screenshot_path: str
    screenshot_sha256: str


@dataclass(frozen=True)
class Action:
    name: str
    payload: dict


@dataclass
class AvlState:
    activated: bool = False
    chat_selected: bool = False
    message_pasted: bool = False
    sent: bool = False
    done: bool = False

