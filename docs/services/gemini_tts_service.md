# 📄 `app/services/gemini_tts_service.py` — Gemini Flash Text-to-Speech

> **Back to:** [APP_DOCUMENTATION.md](../../APP_DOCUMENTATION.md)

---

## Overview

`gemini_tts_service.py` implements **Text-to-Speech (TTS)** using Google's **Gemini 2.5 Flash TTS** model. It supports multiple API keys with **automatic round-robin load balancing** to handle quota limits.

---

## Class: `GeminiTTSService`

### Initialization

Reads `GOOGLE_STT_KEYS` from settings (comma-separated list of Google API keys).

```python
raw_keys = self.settings.google_stt_keys
self.api_keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
```

- Model: `gemini-2.5-flash-preview-tts`
- Default voice: `"Puck"` (a built-in Gemini prebuilt voice)

---

## Key Methods

### `text_to_speech(text, voice_id, language, output_format) → bytes | None`

Converts text to audio. Returns **WAV bytes** or `None` on failure.

**Steps:**
1. Validates text is not empty.
2. Builds `GenerateContentConfig` with `AUDIO` response modality and voice config.
3. Calls `_safe_api_call()` which handles key rotation on failure.
4. Extracts `inline_data.data` from the Gemini response candidates.
5. Decodes PCM audio bytes (base64 if needed).
6. **Wraps PCM → WAV** using Python's `wave` module:
   - 1 channel (mono)
   - Sample width: 2 bytes (16-bit)
   - Frame rate: 24,000 Hz

```python
audio_bytes = await gemini_tts.text_to_speech("ನಮಸ್ಕಾರ", language="kn")
# Returns WAV bytes
```

---

### `save_audio_to_file(audio_data, file_path) → bool`

Writes the audio bytes to a file on disk.

```python
gemini_tts.save_audio_to_file(audio_bytes, "/path/to/output.wav")
```

---

## Load Balancing

### `_rotate_key()`

Switches to the next API key in round-robin fashion:
```python
self.current_index = (self.current_index + 1) % len(self.api_keys)
```

### `_safe_api_call(func, *args, **kwargs)`

Wraps any API call with automatic failover:
- Tries current key.
- On failure: rotates to next key and retries.
- After exhausting all keys: raises `RuntimeError("All TTS API keys failed.")`.

---

## Output Format

The service **always outputs WAV** regardless of the `output_format` parameter (the conversion is hardcoded to WAV wrapping).

> Note: `conversation_nodes.py` saves the audio as `.mp3` extension even though it receives WAV bytes from this service. This is a naming inconsistency — the actual content is WAV format.

---

## Current Usage Status

> ⚠️ `GeminiTTSService` is **initialized** in `ConversationNodes` but is **NOT the active TTS** called in `generate_audio_response()`. The active TTS is `ElevenLabsService`. Gemini TTS can be swapped in as the active TTS by replacing the call in the node.

---

## Global Instance

```python
_gemini_tts_service = GeminiTTSService()

def get_gemini_tts_service() -> GeminiTTSService:
    return _gemini_tts_service
```

---

## Related Files

| File | Role |
|---|---|
| [core/config.py](../core/config.md) | Provides `GOOGLE_STT_KEYS` (shared pool with STT) |
| [services/elevenlabs_service.py](elevenlabs_service.md) | Active TTS (currently replacing Gemini TTS) |
| [nodes/conversation_nodes.py](../nodes/conversation_nodes.md) | Initializes this service but uses ElevenLabs instead |
