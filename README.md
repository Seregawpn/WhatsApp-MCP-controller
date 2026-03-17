# WhatsApp MCP Controller

`WhatsApp MCP Controller` is a local macOS automation tool for WhatsApp Desktop.
It is designed to control the desktop app from your machine through system automation, with two operating modes:

- a direct controller for selecting chats, pasting messages, and optionally sending them
- an AVL mode (`Agent Vision Loop`) for screenshot-driven interaction

This repository is for local desktop control. It is not an official WhatsApp API integration.

## What it can do

- open WhatsApp Desktop
- optionally switch to a contact by name or phone number
- paste a message into the current chat
- send the message or leave it as draft text in the composer
- run a dry check without UI side effects
- run a screenshot-based AVL workflow
- use a deterministic analyzer or a Gemini-backed analyzer in AVL mode

## Requirements

- macOS
- WhatsApp Desktop installed
- Python 3.10+
- Accessibility permission for Terminal, Codex, or the app that runs the controller

## Installation

Clone the repository:

```bash
git clone https://github.com/Seregawpn/WhatsApp-MCP-controller.git
cd WhatsApp-MCP-controller
```

Create a virtual environment and install the package:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -U pip
python3 -m pip install -e .
```

After installation, the console commands are available:

```bash
whatsapp-controller --help
whatsapp-controller-avl --help
```

You can also run the project without installation:

```bash
python3 main.py --help
python3 main_avl.py --help
PYTHONPATH=src python3 -m whatsapp_test --help
```

## First-time setup

1. Open WhatsApp Desktop.
2. Grant Accessibility permission in macOS:
   `System Settings -> Privacy & Security -> Accessibility`
3. Add the terminal or runtime you use to the allowed apps.
4. Run a dry check first:

```bash
python3 main.py --message "Test message" --dry-run
```

## Direct controller mode

Send a message to the currently open chat:

```bash
python3 main.py --message "Hello from WhatsApp MCP Controller"
```

Paste a message without sending:

```bash
python3 main.py --message "Draft message" --no-send
```

Select a contact by name:

```bash
python3 main.py --contact "John Smith" --message "Hello"
```

Select a contact by phone number:

```bash
python3 main.py --contact "+15551234567" --message "Hello"
```

Run a dry-run:

```bash
python3 main.py --contact "John Smith" --message "Hello" --dry-run
```

## AVL mode

AVL mode runs a loop like:

`screenshot -> analyze -> action -> screenshot`

Basic run:

```bash
python3 main_avl.py --contact "Sophia" --message "Test from AVL" --auto-send
```

Dry-run AVL:

```bash
python3 main_avl.py --contact "Sophia" --message "Test from AVL" --dry-run
```

Deterministic AVL:

```bash
python3 main_avl.py --contact "Sophia" --message "Test from AVL" --deterministic
```

Gemini-backed AVL:

```bash
export GEMINI_API_KEY="your_key_here"
python3 main_avl.py --contact "Sophia" --message "Test from AVL" --auto-send --llm-model "gemini-2.0-flash"
```

Or via local config:

```bash
cp config.env.example config.env
# add GEMINI_API_KEY=your_key_here
python3 main_avl.py --contact "Sophia" --message "Test from AVL" --auto-send
```

API key priority:

1. `--api-key`
2. environment variable from `--api-key-env`
3. `config.env`

By default, AVL screenshots are written to `avl_runs/`.

## Project structure

- `main.py`
  Bootstrap entrypoint for direct controller mode.
- `main_avl.py`
  Bootstrap entrypoint for AVL mode.
- `src/whatsapp_test/__main__.py`
  Main CLI for direct WhatsApp Desktop control.
- `src/whatsapp_test/avl_main.py`
  CLI for the AVL workflow.
- `src/whatsapp_test/coordinator.py`
  Main orchestration logic.
- `src/whatsapp_test/permission_gate.py`
  Accessibility permission checks.
- `src/whatsapp_test/whatsapp_adapter.py`
  Low-level AppleScript and clipboard automation.

## Important notes

- This project is macOS-only.
- This is desktop UI automation, not an official network API.
- UI updates in WhatsApp Desktop can affect selectors and focus behavior.
- Accessibility permission is required for reliable execution.
- The safest workflow is to test with `--dry-run` or `--no-send` first.

## Publish-safe usage

- Do not commit `config.env`
- Do not commit `avl_runs/`
- Do not commit screenshots, local caches, or generated build artifacts
- Keep personal contacts and personal test data out of the repository
