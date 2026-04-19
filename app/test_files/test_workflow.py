#!/usr/bin/env python3
"""
Test core/workflow.py independently, with support for text, image, and audio.

Usage examples (PowerShell):
  # Basic text test
  & "d:/ai agent/.venv/Scripts/python.exe" "d:/ai agent/RaithaMithra/app/test_workflow.py" "Hello there"

  # With image
  & "d:/ai agent/.venv/Scripts/python.exe" "d:/ai agent/RaithaMithra/app/test_workflow.py" "Describe this" --image "d:/ai agent/demo.jpg"

  # With audio only
  & "d:/ai agent/.venv/Scripts/python.exe" "d:/ai agent/RaithaMithra/app/test_workflow.py" --audio "d:/ai agent/demo.wav"

  # Kannada
  & "d:/ai agent/.venv/Scripts/python.exe" "d:/ai agent/RaithaMithra/app/test_workflow.py" "kn: ನಮಸ್ಕಾರ"

  # Direct mode (bypasses LangGraph)
  & "d:/ai agent/.venv/Scripts/python.exe" "d:/ai agent/RaithaMithra/app/test_workflow.py" "Test" --direct
"""

import os
import sys
import sys
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import asyncio
from pathlib import Path

from dotenv import load_dotenv

# Ensure UTF-8 output on Windows terminals
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def setup_env_and_path() -> None:
    here = Path(__file__).resolve()
    tests_dir = here.parent
    app_dir = tests_dir.parent
    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))

    # Load .env from project root if present
    root = app_dir.parent
    load_dotenv(root / ".env")


async def test_workflow(
    text: str,
    language: str = "en",
    image_path: str | None = None,
    audio_path: str | None = None,
    direct: bool = False,
) -> dict:
    from core.workflow import get_workflow

    workflow = get_workflow()
    session_id = f"workflow_test_{os.getpid()}"
    user_id = "workflow_tester"

    print(f"Mode: {'Direct (bypass LangGraph)' if direct else 'LangGraph workflow'}")
    print(f"Session: {session_id}")
    print(f"Language: {language}")
    if image_path:
        print(f"Image: {image_path}")
    if audio_path:
        print(f"Audio: {audio_path}")
        if not text:
            print("Mode: Audio-only → expecting STT transcription")
    print(f"Input: {text}")
    print()

    if direct:
        result = await workflow._run_direct_conversation(
            user_input=text,
            session_id=session_id,
            user_id=user_id,
            language=language,
            image_url=image_path,
            audio_url=audio_path,  # 🔹 pass audio path directly
        )
    else:
        result = await workflow.run_conversation(
            user_input=text,
            session_id=session_id,
            user_id=user_id,
            language=language,
            image_url=image_path,
            audio_url=audio_path,  # 🔹 pass audio path directly
        )

    return result


def parse_args() -> tuple[str, str | None, str | None, bool]:
    args = sys.argv[1:]
    image_path = None
    audio_path = None
    direct = False

    if "--image" in args:
        idx = args.index("--image")
        if idx + 1 < len(args):
            image_path = args[idx + 1].strip()
            del args[idx: idx + 2]

    if "--audio" in args:
        idx = args.index("--audio")
        if idx + 1 < len(args):
            audio_path = args[idx + 1].strip()
            del args[idx: idx + 2]

    if "--direct" in args:
        direct = True
        args.remove("--direct")

    text = " ".join(args).strip()
    return text, image_path, audio_path, direct


def main() -> None:
    setup_env_and_path()
    raw, image_path, audio_path, direct = parse_args()

    language = "en"
    text = raw
    if raw.startswith("kn:"):
        language = "kn"
        text = raw[3:].strip()

    # Validate audio file if provided
    if audio_path and not os.path.exists(audio_path):
        print(f"❌ Audio file not found: {audio_path}")
        return

    try:
        result = asyncio.run(
            test_workflow(
                text,
                language=language,
                image_path=image_path,
                audio_path=audio_path,
                direct=direct,
            )
        )

        print("=" * 50)
        print("WORKFLOW RESULT")
        print("=" * 50)
        print(f"Session ID: {result.get('session_id')}")
        print(f"Intent: {result.get('intent')}")
        print(f"Language: {result.get('language')}")
        print(f"Audio Generated: {result.get('audio_generated')}")
        if result.get('audio_path'):
            print(f"Audio Path: {result.get('audio_path')}")
        print(f"Memory Saved: {result.get('memory_saved')}")
        if result.get('memory_id'):
            print(f"Memory ID: {result.get('memory_id')}")
        if result.get('error'):
            print(f"Error: {result.get('error')}")
        print()
        label = "TRANSCRIPTION" if (audio_path and (not text)) else "ASSISTANT RESPONSE"
        print(label + ":")
        print("-" * 30)
        print(result.get('assistant_response', '<no response>'))
        print("-" * 30)

    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
