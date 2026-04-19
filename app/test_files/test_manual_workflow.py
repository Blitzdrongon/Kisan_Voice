#!/usr/bin/env python3
"""
Interactive manual workflow tester.

Type a message, and it will run through KisanVoice's workflow and print the response.
Type 'exit' to quit.
"""

import os
import sys
import asyncio
from pathlib import Path

from dotenv import load_dotenv


def setup_paths_and_env() -> None:
    """Ensure we can import app modules and env is loaded."""
    here = Path(__file__).resolve()
    app_dir = here.parent
    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))

    # Load .env from project root if present
    root = app_dir.parent
    load_dotenv(root / ".env")


async def run_once(user_text: str, language: str = "en", image_path: str | None = None) -> dict:
    from core.workflow import get_workflow

    workflow = get_workflow()
    session_id = f"manual_{os.getpid()}"
    user_id = "manual_tester"

    result = await workflow.run_conversation(
        user_input=user_text,
        session_id=session_id,
        user_id=user_id,
        language=language,
        image_url=image_path,
    )
    return result


def main() -> None:
    setup_paths_and_env()

    print("KisanVoice Manual Workflow Tester")
    print("- Type your message and press Enter")
    print("- Type 'exit' to quit")
    print("- Optionally prefix with 'kn:' for Kannada, e.g., 'kn: ನಮಸ್ಕಾರ'\n")

    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not raw:
            continue
        if raw.lower() in {"exit", "quit", ":q"}:
            break

        language = "en"
        text = raw
        if raw.startswith("kn:"):
            language = "kn"
            text = raw[3:].strip()

        try:
            result = asyncio.run(run_once(text, language=language))
        except Exception as e:
            print(f"[Error] {e}")
            continue

        assistant = (result.get("assistant_response") or "").strip()
        intent = result.get("intent") or "unknown"
        audio_generated = bool(result.get("audio_generated"))
        audio_path = result.get("audio_path")

        print("\n[Result]")
        print(f"Intent: {intent}")
        print(f"Response: {assistant}")
        if audio_generated and audio_path:
            print(f"Audio: {audio_path}")
        print()


if __name__ == "__main__":
    main()


