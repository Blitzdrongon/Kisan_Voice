#!/usr/bin/env python3
"""
Quick test for GeminiTTSService.

Usage (PowerShell):
  & "d:/ai agent/.venv/Scripts/python.exe" "d:/ai agent/RaithaMithra/app/test files/test_gemini_tts.py" "Hello from Gemini TTS" mp3

Args:
  1) text (default: "Hello from Gemini TTS")
  2) format (mp3|wav|ogg) (default: mp3)
"""

import os
import sys
import asyncio
from pathlib import Path

# Ensure UTF-8 output on Windows terminals
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from dotenv import load_dotenv


def setup_env_and_path() -> None:
    here = Path(__file__).resolve()
    tests_dir = here.parent
    app_dir = tests_dir.parent
    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))

    # Load .env from project root if present
    root = app_dir.parent
    load_dotenv(root / ".env")


async def run_test(text: str, output_format: str = "mp3") -> None:
    from services.gemini_tts_service import get_gemini_tts_service

    tts = get_gemini_tts_service()

    print(f"Model: {tts.model}")
    print(f"Format: {output_format}")
    print(f"Text: {text}")

    audio_bytes = await tts.text_to_speech(text=text, output_format=output_format)
    if not audio_bytes:
        print("❌ No audio generated")
        return

    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)
    out_path = uploads_dir / f"gemini_tts_test.{output_format}"

    ok = tts.save_audio_to_file(audio_bytes, str(out_path))
    if not ok:
        print("❌ Failed to save audio file")
        return

    print("✅ Audio generated and saved:")
    print(str(out_path))


def parse_args() -> tuple[str, str]:
    args = sys.argv[1:]
    text = args[0] if args[:1] else "Hello from Gemini TTS"
    fmt = args[1].lower() if len(args) > 1 else "mp3"
    if fmt not in {"mp3", "wav", "ogg"}:
        fmt = "mp3"
    return text, fmt


def main() -> None:
    setup_env_and_path()
    text, fmt = parse_args()

    try:
        asyncio.run(run_test(text, fmt))
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
