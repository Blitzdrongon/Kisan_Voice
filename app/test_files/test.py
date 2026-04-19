#!/usr/bin/env python3
"""
Standalone tester for services/groq_service.py

Usage (PowerShell):
  & "d:/ai agent/.venv/Scripts/python.exe" "d:/ai agent/RaithaMithra/app/test.py" "your prompt here"

If no prompt is provided, a default will be used.
"""

import os
import sys
import asyncio
from pathlib import Path

from dotenv import load_dotenv


def setup_env_and_path() -> None:
    here = Path(__file__).resolve()
    app_dir = here.parent
    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))

    # Load .env from project root if present
    root = app_dir.parent
    load_dotenv(root / ".env")


async def main_async(prompt: str, language: str = "en") -> None:
    from services.groq_service import get_groq_service

    service = get_groq_service()

    print("🔎 GROQ Health:", "✅" if service.is_healthy() else "⚠️ Unhealthy or unreachable")
    print("Model:", "llama-3.3-70b-versatile")
    print("Language:", language)
    print("API Key present:", "✅" if service.api_key else "❌ Missing")

    print(f"\n→ Generating text for: '{prompt}'...")
    try:
        text = await service.generate_text(prompt=prompt, language=language)
        print(f"\n[Response]\n{text or '<empty>'}")
        print(f"Response length: {len(text) if text else 0}")
    except Exception as e:
        print(f"❌ Error generating text: {e}")
        import traceback
        traceback.print_exc()


def main() -> None:
    setup_env_and_path()

    # Accept prompt from CLI or default
    if len(sys.argv) > 1:
        raw = " ".join(sys.argv[1:]).strip()
    else:
        raw = "Explain in two sentences what this app does."

    language = "en"
    if raw.startswith("kn:"):
        language = "kn"
        raw = raw[3:].strip()

    asyncio.run(main_async(raw, language=language))


if __name__ == "__main__":
    main()


