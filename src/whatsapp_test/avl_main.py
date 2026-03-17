import argparse
import os
import sys

from whatsapp_test.avl.analyzer import build_analyzer
from whatsapp_test.avl.coordinator import AvlCoordinator
from whatsapp_test.avl.models import AvlGoal
from whatsapp_test.avl.toolkit import AvlToolkit
from whatsapp_test.permission_gate import PermissionGate
from whatsapp_test.whatsapp_adapter import WhatsAppAdapter


def _load_key_from_env_file(path: str, env_name: str) -> str | None:
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                if key.strip() == env_name:
                    return val.strip().strip('"').strip("'")
    except OSError:
        return None
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="whatsapp-controller-avl",
        description="AVL controller for WhatsApp Desktop on macOS.",
    )
    parser.add_argument("--contact", required=True, help="WhatsApp contact name or phone")
    parser.add_argument("--message", required=True, help="Message text")
    parser.add_argument("--auto-send", action="store_true", help="Send with Enter at end")
    parser.add_argument(
        "--max-steps",
        type=int,
        default=8,
        help="Max AVL iterations",
    )
    parser.add_argument(
        "--out-dir",
        default="avl_runs",
        help="Directory for captured screenshots",
    )
    parser.add_argument(
        "--llm-model",
        default="gemini-2.0-flash",
        help="Gemini model for analyzer",
    )
    parser.add_argument(
        "--api-key",
        help="Gemini API key (highest priority)",
    )
    parser.add_argument(
        "--api-key-env",
        default="GEMINI_API_KEY",
        help="Environment variable name for Gemini key",
    )
    parser.add_argument(
        "--config-env",
        default="config.env",
        help="Path to env-style config file (e.g., GEMINI_API_KEY=...)",
    )
    parser.add_argument(
        "--deterministic",
        action="store_true",
        help="Disable LLM and use deterministic analyzer only",
    )
    parser.add_argument("--dry-run", action="store_true", help="No UI side effects")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    gate = PermissionGate()
    permission = gate.check()
    if not permission.accessibility_ok:
        print(f"ERROR: {permission.details}", file=sys.stderr)
        return 1

    out_dir = args.out_dir
    if not os.path.isabs(out_dir):
        out_dir = os.path.join(os.getcwd(), out_dir)

    api_key = args.api_key
    if not api_key:
        api_key = os.environ.get(args.api_key_env)
    if not api_key:
        cfg_path = args.config_env
        if not os.path.isabs(cfg_path):
            cfg_path = os.path.join(os.getcwd(), cfg_path)
        api_key = _load_key_from_env_file(cfg_path, args.api_key_env)

    goal = AvlGoal(
        contact=args.contact,
        message=args.message,
        auto_send=args.auto_send,
        max_steps=args.max_steps,
        out_dir=out_dir,
        dry_run=args.dry_run,
    )
    toolkit = AvlToolkit(adapter=WhatsAppAdapter(), out_dir=goal.out_dir, dry_run=goal.dry_run)
    analyzer = build_analyzer(
        model=args.llm_model,
        force_deterministic=args.deterministic,
        api_key=api_key,
    )
    coordinator = AvlCoordinator(toolkit=toolkit, analyzer=analyzer)
    try:
        print(coordinator.run(goal))
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
