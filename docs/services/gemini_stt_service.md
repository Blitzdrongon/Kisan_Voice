# 📄 `app/services/gemini_stt_service.py` — Gemini Speech-to-Text

> **Back to:** [APP_DOCUMENTATION.md](../../APP_DOCUMENTATION.md)

---

## Overview

`gemini_stt_service.py` implements **Speech-to-Text (STT)** transcription using **Google Gemini 2.5 Flash**. It supports multiple API keys with round-robin load balancing via the `GeminiKeyBalancer` helper.

---

## Classes

### `GeminiKeyBalancer`

A simple round-robin load balancer for multiple API keys.

```python
balancer = GeminiKeyBalancer(["key1", "key2", "key3"])
next_key = balancer.next_key()  # Cycles: key1 → key2 → key3 → key1 → ...
```

---

### `GeminiSTTService`

The main STT service.

**Initialization:**
- Reads `GOOGLE_STT_KEYS` from settings (comma-separated).
- Creates a `GeminiKeyBalancer` with those keys.
- Model: `gemini-2.5-flash`

---

## Key Methods

### `transcribe(file_path, language, prompt) → str`

Transcribes a local audio file and returns plain text.

**Steps:**
1. Validates file exists.
2. Detects MIME type from extension using `_guess_mime_type()`.
3. Gets next API key from `GeminiKeyBalancer`.
4. Creates a new Gemini client with that key.
5. **Uploads audio** to Gemini Files API: `client.files.upload(file=file_path)`.
6. Sends a generate-content request with a strict transcription prompt.
7. Returns `response.text` or aggregates from candidates.

**Default transcription prompt:**
```
Transcribe the audio EXACTLY as spoken. Do NOT translate. Do NOT interpret.
Keep the original language exactly the same. Output only the transcript.
```

---

### `_guess_mime_type(file_path) → str`

Maps file extensions to MIME types:

| Extension | MIME Type |
|---|---|
| `.mp3`, `.mpeg` | `audio/mp3` |
| `.wav` | `audio/wav` |
| `.ogg` | `audio/ogg` |
| `.flac` | `audio/flac` |
| `.aac` | `audio/aac` |
| `.aiff`, `.aif` | `audio/aiff` |
| (default) | `audio/mp3` |

---

## Usage in Pipeline

Called in `conversation_nodes.py` inside `_handle_voice_request()`:

```python
transcription = await self.gemini_stt_service.transcribe(audio_url, language=language)
if transcription:
    return await self._handle_general_conversation(transcription, language, context)
```

Also called in `workflow.py` for audio pre-processing before the pipeline starts.

---

## Difference vs `whisper_services.py`

| Feature | `gemini_stt_service.py` | `whisper_services.py` |
|---|---|---|
| Provider | Google Gemini | Groq Whisper |
| Model | `gemini-2.5-flash` | `whisper-large-v3-turbo` |
| Input method | Files API upload | Binary file POST |
| Multi-key LB | ✅ Yes | ❌ No (single key) |
| Used for | Voice request intent | Audio pre-transcription in workflow |

---

## Global Instance

```python
_gemini_stt_service = GeminiSTTService()

def get_gemini_stt_service() -> GeminiSTTService:
    return _gemini_stt_service
```

---

## Related Files

| File | Role |
|---|---|
| [core/config.py](../core/config.md) | Provides `GOOGLE_STT_KEYS` |
| [services/whisper_services.py](whisper_services.md) | Alternative Groq-based STT |
| [nodes/conversation_nodes.py](../nodes/conversation_nodes.md) | Calls `transcribe()` for voice requests |
| [core/workflow.py](../core/workflow.md) | Calls Whisper for audio pre-transcription |
