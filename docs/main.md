# 📄 `app/main.py` — Chainlit Web Chat Entry Point

> **Back to:** [APP_DOCUMENTATION.md](../APP_DOCUMENTATION.md)

---

## Overview

`main.py` is the **primary Chainlit web application** for RaithaMithra. It is the entry point for the browser-based chat interface and ties together all services (LLM, TTS, STT, weather, memory, workflow).

When you run RaithaMithra via Chainlit (`chainlit run app/main.py`), this file takes control.

---

## How to Run

```bash
chainlit run app/main.py
```

---

## Imports & Initialization

On startup, the following are initialized as **global singletons**:

| Object | Source | Purpose |
|---|---|---|
| `settings` | `core.config` | App-wide config & API keys |
| `memory_manager` | `core.memory` | SQLite + Qdrant memory |
| `workflow` | `core.workflow` | LangGraph conversation pipeline |
| `groq_service` | `services.groq_service` | LLM + audio transcription |
| `elevenlabs_service` | `services.elevenlabs_service` | Text-to-speech audio |
| `weather_service` | `services.weather_service` | OpenWeather data |

An `uploads/` directory is auto-created on startup to store temporary audio files.

---

## Session Management

```python
user_sessions: Dict[str, Dict[str, Any]] = {}
```

An in-memory dictionary keyed by `user_id`. Each session stores:
- `session_id` — unique identifier (`session_<user_id>_<timestamp>`)
- `user_id` — Chainlit user identifier
- `language` — current detected language (`"kn"` or `"en"`)
- `created_at` — ISO timestamp
- `conversation_history` — list of past exchanges

---

## Chainlit Hooks

### `@cl.on_chat_start` — `on_chat_start()`

Triggered when a user opens the chat.

**Steps:**
1. Gets user ID from Chainlit session.
2. Creates a new session entry in `user_sessions`.
3. Sends a bilingual welcome message (Kannada + English) listing all features.

---

### `@cl.on_message` — `on_message(message)`

Triggered on every user message. This is the main handler.

**Full flow:**

```
Message received
    │
    ├── message.elements contains audio?
    │       ├── Show audio element back to user (echo)
    │       ├── Save audio file to uploads/
    │       ├── Call groq_service.transcribe_audio(path) → transcribed text
    │       ├── Show transcribed text as user message
    │       └── Use transcription as user_input
    │
    ├── message.elements contains image?
    │       ├── Save image to uploads/
    │       ├── Call groq_service.analyze_image(path)
    │       └── Append "[Image Analysis: ...]" to user_input
    │
    ├── Detect language (Kannada script chars → "kn", else "en")
    │
    ├── workflow.run_conversation(user_input, session_id, user_id, language, image_url)
    │
    ├── Send assistant_response as text message
    │
    └── If audio_path in response → send cl.Audio element (auto-play) → delete file
```

**Key behaviour:**
- Audio and image elements are processed **before** the text workflow call.
- Language detection happens per message and updates the session.
- After response, the exchange is appended to `user_sessions[user_id]["conversation_history"]`.

---

### `@cl.on_chat_end` — `on_chat_end()`

Triggered when a user closes the chat. Removes the user's session from `user_sessions` to free memory.

---

## Language Detection Logic

```python
kannada_chars = set('ಅಆಇಈಉಊಋ...')
if any(char in kannada_chars for char in user_input):
    language = "kn"
else:
    language = "en"
```

Simple Unicode character-set check. If any Kannada character is found → Kannada. Otherwise → English.

---

## Audio Handling Details

### Input (Voice → Text)
1. Audio bytes extracted from `message.elements`.
2. Saved to `uploads/voice_input_<uuid>.wav`.
3. Sent to `groq_service.transcribe_audio()` (Groq Whisper).
4. Temp file deleted in `finally` block.

### Output (Text → Audio)
1. Workflow returns `audio_path` (absolute path to `.mp3` file).
2. Bytes read from file → wrapped in `cl.Audio(auto_play=True)`.
3. Audio file is deleted after sending.

---

## Error Handling

Every hook is wrapped in `try/except`. On any error:
- Logs via `loguru` logger.
- Sends a user-facing error in the detected language:
  - Kannada: `"ಕ್ಷಮಿಸಿ, ನಿಮ್ಮ ಸಂದೇಶವನ್ನು ಸಂಸ್ಕರಿಸಲು ದೋಷ ಸಂಭವಿಸಿದೆ."`
  - English: `"Sorry, an error occurred processing your message."`

---

## Difference from `main_simple.py`

| Feature | `main.py` | `main_simple.py` |
|---|---|---|
| Full workflow | ✅ LangGraph pipeline | ❌ Keyword-based demo |
| Real Groq LLM | ✅ | ❌ Hardcoded replies |
| Real STT | ✅ Groq Whisper | ❌ Placeholder text |
| Real TTS | ✅ Via workflow | ❌ None |
| Use case | Production | Testing without API keys |

---

## Related Files

| File | Role |
|---|---|
| [core/workflow.py](core/workflow.md) | Conversation pipeline called by this file |
| [core/memory.py](core/memory.md) | Memory system initialized here |
| [services/groq_service.py](services/groq_service.md) | LLM + STT called directly for audio |
| [main_simple.py](main_simple.md) | Simplified demo alternative |
