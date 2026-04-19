# 📄 `app/services/groq_service.py` — Groq LLM, STT & Vision Service

> **Back to:** [APP_DOCUMENTATION.md](../../APP_DOCUMENTATION.md)

---

## Overview

`groq_service.py` is the **primary AI engine** for KisanVoice. It wraps the Groq API for three capabilities:

1. **Text generation** — LLM responses using `llama-3.3-70b-versatile`
2. **Audio transcription** — Speech-to-text using Groq Whisper
3. **Image analysis** — Vision understanding using `llama-3.2-90b-vision-preview`

All API calls are made via `httpx` as async HTTP requests to the Groq OpenAI-compatible API.

---

## Setup

Reads `GROQ_API_KEY` from settings. Raises `ValueError` if missing.

```python
from services.groq_service import get_groq_service

groq = get_groq_service()
```

Base URL: `https://api.groq.com/openai/v1`

---

## Methods

### `generate_text(prompt, model, max_tokens, temperature, language, context) → str`

Generates a text response using the Groq chat completions API.

**Default model:** `llama-3.3-70b-versatile`  
**Default max_tokens:** `500`  
**Default temperature:** `0.7`

#### System Prompt — "KISAN VOICE"

The system prompt defines the assistant persona:

> *"You are KISAN VOICE, an AI agriculture assistant helping farmers mainly in North Karnataka and nearby regions of India."*

Key rules embedded in the prompt:
- Always reply **only in the `{language}` language**.
- Focus on Karnataka crops: Jowar, Bajra, Cotton, Tur, Groundnut, Maize, Paddy, Onion, Sugarcane.
- Classify intent before answering (crop_advice, pest_disease, fertilizer, etc.).
- If critical info is missing (crop name, stage), ask ONE follow-up question.
- Format responses with: ⭐ Key Points → ➤ What To Do → ⚠ Warning → ❌ Avoid → 🌱 Extra Tip.
- Never give pesticide dosage without units.
- Keep answers under ~120 words.
- Follow ICAR / KVK recommended practices.

#### User Prompt Structure
```
CONTEXT:
<conversation history + preferences>

QUESTION:
<user_input>

ANSWER:
```

#### Response Extraction

Handles both OpenAI-style chat completion format and plain text format:
```python
generated_text = choice0.get("message", {}).get("content") or choice0.get("text")
```

---

### `transcribe_audio(audio_file_path) → str`

Transcribes a local audio file using **Groq Whisper** (`whisper-1` model).

```python
text = await groq.transcribe_audio("/path/to/voice_input.wav")
```

**Steps:**
1. Validates file exists.
2. Opens file in binary mode.
3. POSTs to `/audio/transcriptions` with `model=whisper-1`.
4. Returns the transcribed text string.

> Note: `whisper_services.py` uses `whisper-large-v3-turbo` — this method uses the older `whisper-1`. Both target the Groq transcription endpoint.

---

### `analyze_image(image_path, prompt, model, language) → str`

Analyzes an image using **Groq's vision model** (`llama-3.2-90b-vision-preview`).

**Steps:**
1. Reads and base64-encodes the image file.
2. Detects MIME type from extension (`.jpg`, `.png`, `.gif`, `.webp`).
3. Sends a multi-modal message with image + text prompt.
4. Returns the analysis text.

```python
analysis = await groq.analyze_image(
    image_path="/path/to/farm_image.jpg",
    prompt="What crop disease do you see?",
    language="kn"
)
```

> Note: `image_anylsis.py` (Gemini) is the **preferred** image analysis service in the pipeline. This method in groq_service is called directly from `main.py` for initial image description at message intake.

---

### `get_available_models() → List[str]`

Returns a static list of supported Groq models:
```python
["llama-3.3-70b-versatile", "llama-3.2-90b-vision-preview", "mixtral-8x7b-32768", "gemma2-9b-it"]
```

---

### `is_healthy() → bool`

Synchronous health check — GETs `/models` endpoint. Returns `True` if API responds with 200.

---

## Error Handling

All methods return a bilingual error message on failure:
- Kannada: `"ಕ್ಷಮಿಸಿ, ಒಂದು ದೋಷ ಸಂಭವಿಸಿದೆ."`
- English: `"Sorry, an error occurred."`

---

## Global Instance

```python
groq_service = GroqService()

def get_groq_service() -> GroqService:
    return groq_service
```

---

## Related Files

| File | Role |
|---|---|
| [core/config.py](../core/config.md) | Provides `groq_api_key` |
| [nodes/conversation_nodes.py](../nodes/conversation_nodes.md) | Calls `generate_text()` for general conversation |
| [main.py](../main.md) | Calls `transcribe_audio()` and `analyze_image()` directly |
| [services/whisper_services.py](whisper_services.md) | Alternative Whisper with newer model |
