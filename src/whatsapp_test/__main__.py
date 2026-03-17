import argparse
import sys

from .coordinator import InteractionCoordinator
from .models import RunRequest
from .permission_gate import PermissionGate
from .whatsapp_adapter import WhatsAppAdapter


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="whatsapp-controller",
        description="Local WhatsApp Desktop controller for macOS.",
    )
    parser.add_argument(
        "--contact",
        help="WhatsApp contact name or phone number (optional)",
    )
    parser.add_argument("--message", required=True, help="Message to paste/send")
    parser.add_argument(
        "--no-send",
        action="store_true",
        help="Paste only, do not press Enter",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only run permission and flow checks",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    coordinator = InteractionCoordinator(PermissionGate(), WhatsAppAdapter())
    req = RunRequest(
        contact=args.contact,
        message=args.message,
        send=not args.no_send,
        dry_run=args.dry_run,
    )
    try:
        result = coordinator.execute(req)
        print(result)
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
