#!/usr/bin/env python3
"""
Redesigned Gemini TTS test script

- Loads .env
- Accepts text and optional voice name
- Forces WAV output (per Gemini TTS preview spec)
- Saves to uploads/<timestamp>_gemini_tts_<voice>.wav
- Prints helpful diagnostics

Usage (PowerShell):
  & "d:/ai agent/.venv/Scripts/python.exe" "d:/ai agent/KisanVoice/app/test files/test_gemini_tts_v2.py" "Say cheerfully: Have a wonderful day!" Puck

Args:
  1) text (default: "Say cheerfully: Have a wonderful day!")
  2) voice_name (default: Puck)
"""

import os
import sys
import asyncio
from datetime import datetime
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


def parse_args() -> tuple[str, str]:
    args = sys.argv[1:]
    text = args[0] if args[:1] else "Say cheerfully: Have a wonderful day!"
    voice = args[1] if len(args) > 1 else "Puck"
    return text, voice


async def run_test(text: str, voice_name: str) -> None:
    from services.gemini_tts_service import get_gemini_tts_service

    # Diagnostics: env
    key = os.environ.get("GOOGLE_API_KEY", "")
    print(f"GOOGLE_API_KEY loaded: {bool(key)}")

    tts = get_gemini_tts_service()
    print(f"Model: {tts.model}")
    print(f"Voice: {voice_name}")
    print(f"Text: {text}")
    print("Output: WAV (24kHz, mono)")

    # Synthesize
    audio_bytes = await tts.text_to_speech(text=text, voice_id=voice_name, output_format="wav")
    if not audio_bytes:
        print("❌ No audio generated")
        return

    # Save
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_voice = "".join(c for c in voice_name if c.isalnum() or c in ("-","_")).strip() or "voice"
    out_path = uploads_dir / f"{timestamp}_gemini_tts_{safe_voice}.wav"

    ok = tts.save_audio_to_file(audio_bytes, str(out_path))
    if not ok:
        print("❌ Failed to save audio file")
        return

    size_kb = len(audio_bytes) / 1024.0
    print("✅ Audio generated and saved:")
    print(str(out_path))
    print(f"Size: {size_kb:.1f} KB")


def main() -> None:
    setup_env_and_path()

    # Quick SDK version check (best-effort)
    try:
        import google.genai as g
        print(f"google-genai version: {getattr(g, '__version__', 'unknown')}")
    except Exception:
        print("google-genai version: <unavailable>")

    text, voice = parse_args()

    try:
        asyncio.run(run_test(text, voice))
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
