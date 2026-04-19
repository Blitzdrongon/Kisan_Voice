#!/usr/bin/env python3
"""
Test individual conversation nodes.

Usage examples (PowerShell):
  # Run all nodes in sequence
  & "d:/ai agent/.venv/Scripts/python.exe" "d:/ai agent/RaithaMithra/app/test_node.py" "Hello there"

  # Run a specific node only (process|respond|memory|audio)
  & "d:/ai agent/.venv/Scripts/python.exe" "d:/ai agent/RaithaMithra/app/test_node.py" "What's the weather?" --node respond

  # Kannada input
  & "d:/ai agent/.venv/Scripts/python.exe" "d:/ai agent/RaithaMithra/app/test_node.py" "kn: ನಮಸ್ಕಾರ"
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Dict, Any

from dotenv import load_dotenv


def setup_env_and_path() -> None:
    here = Path(__file__).resolve()
    app_dir = here.parent
    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))

    # Load .env from project root if present
    root = app_dir.parent
    load_dotenv(root / ".env")


def make_base_state(text: str, language: str = "en", image_path: str | None = None) -> Dict[str, Any]:
    return {
        "user_input": text,
        "session_id": f"node_test_{os.getpid()}",
        "user_id": "node_tester",
        "language": language,
        "image_url": image_path,
        "messages": [],
        "current_intent": None,
        "assistant_response": None,
        "audio_response_path": None,
        "audio_generated": False,
        "conversation_history": [],
        "user_preferences": {},
        "memory_saved": False,
        "memory_id": None,
        "error": None,
    }


async def run_node_sequence(text: str, language: str = "en", image_path: str | None = None) -> Dict[str, Any]:
    from nodes.conversation_nodes import get_conversation_nodes

    nodes = get_conversation_nodes()
    state = make_base_state(text, language, image_path=image_path)

    print("→ process_user_input")
    state = await nodes.process_user_input(state)
    print("  intent:", state.get("current_intent"))

    print("→ generate_response")
    state = await nodes.generate_response(state)
    print("  assistant:", (state.get("assistant_response") or "").strip())

    print("→ save_to_memory")
    state = await nodes.save_to_memory(state)
    print("  memory_saved:", state.get("memory_saved"), "memory_id:", state.get("memory_id"))

    print("→ generate_audio_response")
    state = await nodes.generate_audio_response(state)
    print("  audio_generated:", state.get("audio_generated"), "audio_path:", state.get("audio_response_path"))

    return state


async def run_single_node(text: str, node: str, language: str = "en", image_path: str | None = None) -> Dict[str, Any]:
    from nodes.conversation_nodes import get_conversation_nodes

    nodes = get_conversation_nodes()
    state = make_base_state(text, language, image_path=image_path)

    if node == "process":
        return await nodes.process_user_input(state)
    if node == "respond":
        # Ensure intent exists for response node
        state = await nodes.process_user_input(state)
        # If an image path is provided, force image_analysis intent
        if image_path:
            state["current_intent"] = "image_analysis"
        return await nodes.generate_response(state)
    if node == "memory":
        # Ensure assistant response exists
        state = await nodes.process_user_input(state)
        state = await nodes.generate_response(state)
        return await nodes.save_to_memory(state)
    if node == "audio":
        # Ensure assistant response exists
        state = await nodes.process_user_input(state)
        state = await nodes.generate_response(state)
        return await nodes.generate_audio_response(state)

    raise ValueError("Unknown node. Use one of: process|respond|memory|audio")


def parse_args() -> tuple[str, str | None, str | None]:
    # Very light argument parsing
    args = sys.argv[1:]
    node = None
    image_path = None
    if "--node" in args:
        idx = args.index("--node")
        if idx + 1 < len(args):
            node = args[idx + 1].strip().lower()
            del args[idx: idx + 2]
    if "--image" in args:
        idx = args.index("--image")
        if idx + 1 < len(args):
            image_path = args[idx + 1].strip()
            del args[idx: idx + 2]
    text = " ".join(args).strip() or "what is the weather in bangalore?"
    return text, node, image_path


def main() -> None:
    setup_env_and_path()
    raw, node, image_path = parse_args()

    language = "en"
    text = raw
    if raw.startswith("kn:"):
        language = "kn"
        text = raw[3:].strip()

    if node:
        state = asyncio.run(run_single_node(text, node=node, language=language, image_path=image_path))
        print("  assistant:", (state.get("assistant_response") or "").strip())
        print("\n[Final State]")
        print({k: state.get(k) for k in ["current_intent", "assistant_response", "memory_saved", "audio_generated", "audio_response_path", "error"]})
    else:
        state = asyncio.run(run_node_sequence(text, language=language, image_path=image_path))
        print("\n[Final State]")
        print({k: state.get(k) for k in ["current_intent", "assistant_response", "memory_saved", "audio_generated", "audio_response_path", "error"]})


if __name__ == "__main__":
    main()


