# 📄 `app/services/whisper_services.py` — Groq Whisper STT Service

> **Back to:** [APP_DOCUMENTATION.md](../../APP_DOCUMENTATION.md)

---

## Overview

`whisper_services.py` implements **Speech-to-Text** transcription using **Groq's Whisper** endpoint. It provides a cleaner, more capable alternative to the basic `transcribe_audio()` method in `groq_service.py`, using the newer `whisper-large-v3-turbo` model.

---

## Class: `SpeechToText`

### Initialization

```python
self.api_key  = settings.groq_api_key
self.base_url = "https://api.groq.com/openai/v1"
```

Uses the same Groq API key as the LLM service. Raises `ValueError` if key is not set.

---

## Methods

### `transcribe_file(audio_file_path, language) → str`

Transcribes a local audio file.

**Model:** `whisper-large-v3-turbo`

**Steps:**
1. Validates file exists.
2. Reads file in binary mode.
3. POSTs to `/audio/transcriptions` with multipart form data.
4. If `language != "auto"`, includes `language` in the form data to hint the model.
5. Returns the transcribed text string.

```python
whisper = get_whisper_service()
text = await whisper.transcribe_file("/path/to/voice.wav", language="kn")
```

**Timeout:** 60 seconds (longer than groq_service's 30s, allowing for larger audio files).

---

### `transcribe_bytes(audio_data, language) → str`

Transcribes in-memory audio bytes.

**Steps:**
1. Writes bytes to a `tempfile.NamedTemporaryFile` with `.wav` suffix.
2. Calls `transcribe_file()` on the temp path.
3. Cleans up the temp file in a `finally` block.

Useful when audio data is already in memory and no file path is available.

```python
text = await whisper.transcribe_bytes(raw_audio_bytes, language="kn")
```

---

## Comparison with `groq_service.transcribe_audio()`

| Feature | `whisper_services.py` | `groq_service.transcribe_audio()` |
|---|---|---|
| Model | `whisper-large-v3-turbo` | `whisper-1` |
| Language hint | ✅ Supported | ❌ Not included |
| In-memory bytes | ✅ `transcribe_bytes()` | ❌ File only |
| Timeout | 60s | 30s |
| Purpose | Workflow audio pre-transcription | Simple in-message transcription |

---

## Where It's Used

Called in `core/workflow.py` for audio pre-transcription before the LangGraph pipeline starts:

```python
if audio_url and not user_input.strip():
    whisper = get_whisper_service()
    transcription = await whisper.transcribe_file(audio_url, language=language)
    user_input = transcription
```

---

## Lazy Global Instance

```python
_whisper_service: Optional[SpeechToText] = None

def get_whisper_service() -> SpeechToText:
    global _whisper_service
    if _whisper_service is None:
        _whisper_service = SpeechToText()
    return _whisper_service
```

Uses **lazy initialization** — the service is only created the first time it's requested.

---

## Related Files

| File | Role |
|---|---|
| [core/config.py](../core/config.md) | Provides `GROQ_API_KEY` |
| [core/workflow.py](../core/workflow.md) | Calls `transcribe_file()` for audio pre-processing |
| [services/groq_service.py](groq_service.md) | Also has Whisper transcription (older model) |
| [services/gemini_stt_service.py](gemini_stt_service.md) | Gemini-based alternative STT |
