#!/usr/bin/env python3
import os
import sys


def _bootstrap_path() -> None:
    root_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(root_dir, "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)


def main() -> int:
    _bootstrap_path()
    from whatsapp_test.__main__ import main as package_main

    return package_main()


if __name__ == "__main__":
    raise SystemExit(main())

