# 📄 `app/services/elevenlabs_service.py` — ElevenLabs Text-to-Speech

> **Back to:** [APP_DOCUMENTATION.md](../../APP_DOCUMENTATION.md)

---

## Overview

`elevenlabs_service.py` wraps the **ElevenLabs TTS API** to convert text to audio. It is currently the **active TTS service** called in the pipeline's audio generation node.

---

## Class: `ElevenLabsService`

### Initialization

```python
self.api_key       = settings.elevenlabs_api_key
self.base_url      = settings.elevenlabs_base_url        # https://api.elevenlabs.io/v1
self.default_voice_id = settings.tts_voice_id           # "21m00Tcm4TlvDq8ikWAM" (Rachel)
```

Headers included in all requests:
```python
{"xi-api-key": api_key, "Content-Type": "application/json"}
```

---

## Methods

### `text_to_speech(text, voice_id, language, output_format) → bytes | None`

Converts text to MP3 audio bytes.

**Model:** `eleven_v3` (ElevenLabs newest model as of implementation)

**Voice settings:**
```python
{
    "stability": 0.5,
    "similarity_boost": 0.75,
    "style": 0.0,
    "use_speaker_boost": True
}
```

**Kannada voice selection:**  
When `language == "kn"`, the service first calls `get_available_voices()` and looks for a voice with "indian" or "south asian" in its name/description. If found, it uses that voice. Otherwise, falls back to `default_voice_id`.

```python
audio_bytes = await elevenlabs.text_to_speech(
    text="ಇಂದಿನ ಹವಾಮಾನ ಚೆನ್ನಾಗಿದೆ.",
    language="kn"
)
# Returns MP3 bytes
```

---

### `text_to_speech_stream(text, voice_id, language) → httpx.Response | None`

Streaming version of TTS — returns the raw `httpx.Response` object with chunked audio data.

Useful for low-latency streaming playback (not yet wired into the pipeline).

---

### `get_available_voices() → dict | None`

GETs the ElevenLabs `/voices` endpoint and returns the full voice list.

---

### `save_audio_to_file(audio_data, file_path) → bool`

Writes MP3 bytes to disk:
```python
elevenlabs.save_audio_to_file(audio_bytes, "/path/to/response.mp3")
```

---

## Integration Point

Called in `conversation_nodes.py` → `generate_audio_response()`:

```python
audio_data = await self.elevenlabs_service.text_to_speech(
    text=response_text,
    language=language
)
if audio_data:
    if self.elevenlabs_service.save_audio_to_file(audio_data, audio_path):
        state["audio_response_path"] = audio_path
        state["audio_generated"] = True
```

---

## Current Status

> ✅ **Active TTS** — This is what generates all audio responses.  
> ⚠️ ElevenLabs may be rate-limited or unavailable depending on your plan. If `text_to_speech()` returns `None`, `audio_generated` is set to `False` and only text is returned.

---

## Known Issues

- The Kannada voice auto-selection (`get_available_voices()`) adds an extra API call per Kannada response. This can be cached for performance.
- ElevenLabs was previously reported as "blocked" in some network environments — if this occurs, switch to `GeminiTTSService` in `conversation_nodes.py`.

---

## Switching to Gemini TTS

To replace ElevenLabs with Gemini TTS in the pipeline, edit `conversation_nodes.py` → `generate_audio_response()`:

```python
# Replace this:
audio_data = await self.elevenlabs_service.text_to_speech(text=response_text, language=language)
if audio_data:
    self.elevenlabs_service.save_audio_to_file(audio_data, audio_path)

# With this:
audio_data = await self.gemini_tts_service.text_to_speech(text=response_text, language=language)
if audio_data:
    self.gemini_tts_service.save_audio_to_file(audio_data, audio_path)
```

---

## Global Instance

```python
elevenlabs_service = ElevenLabsService()

def get_elevenlabs_service() -> ElevenLabsService:
    return elevenlabs_service
```

---

## Related Files

| File | Role |
|---|---|
| [core/config.py](../core/config.md) | Provides `elevenlabs_api_key`, `tts_voice_id`, `elevenlabs_base_url` |
| [services/gemini_tts_service.py](gemini_tts_service.md) | Alternative TTS (Gemini Flash) |
| [nodes/conversation_nodes.py](../nodes/conversation_nodes.md) | Calls this service in `generate_audio_response()` |
