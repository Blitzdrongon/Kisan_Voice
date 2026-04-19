# 📄 `app/core/config.py` — Application Configuration

> **Back to:** [APP_DOCUMENTATION.md](../../APP_DOCUMENTATION.md)

---

## Overview

`config.py` manages all application settings using **Pydantic `BaseSettings`**. It automatically reads values from environment variables and the `.env` file at the project root.

Every other module calls `get_settings()` to access configuration — there is one shared global `Settings` instance.

---

## How It Works

```python
from core.config import get_settings

settings = get_settings()
api_key = settings.groq_api_key
```

Pydantic reads from:
1. Environment variables (highest priority)
2. `.env` file in project root

---

## All Settings

### 🔑 API Keys

| Field | Env Var | Required | Description |
|---|---|---|---|
| `groq_api_key` | `GROQ_API_KEY` | ✅ | Groq LLM + Whisper STT |
| `google_image_keys` | `GOOGLE_IMAGE_KEYS` | ✅ | Gemini keys for image analysis (comma-separated) |
| `google_stt_keys` | `GOOGLE_STT_KEYS` | ✅ | Gemini keys for TTS/STT (comma-separated) |
| `elevenlabs_api_key` | `ELEVENLABS_API_KEY` | ✅ | ElevenLabs TTS |
| `openweather_api_key` | `OPENWEATHER_API_KEY` | ✅ | OpenWeatherMap |

> **Multi-key support:** `GOOGLE_IMAGE_KEYS` and `GOOGLE_STT_KEYS` accept multiple API keys as a comma-separated string:  
> `GOOGLE_IMAGE_KEYS=AIza...key1,AIza...key2,AIza...key3`  
> The services use these for round-robin load balancing.

---

### ⚙️ Application

| Field | Default | Description |
|---|---|---|
| `app_name` | `"KisanVoice"` | Application name |
| `app_version` | `"1.0.0"` | Version string |
| `debug` | `False` | Debug mode |
| `log_level` | `"INFO"` | Logging verbosity |

---

### 🌐 Language

| Field | Default | Description |
|---|---|---|
| `default_language` | `"kn"` | Default language (Kannada) |
| `supported_languages` | `"kn,en"` | Comma-separated list |

---

### 🤖 Models

| Field | Default | Description |
|---|---|---|
| `text_model` | `"llama-3.3-70b-versatile"` | Groq text generation model |
| `vision_model` | `"llama-3.2-90b-vision-preview"` | Groq vision model |
| `tts_voice_id` | `"21m00Tcm4TlvDq8ikWAM"` | ElevenLabs default voice ID |

---

### 🗄️ Memory / Database

| Field | Default | Description |
|---|---|---|
| `qdrant_url` | `"http://localhost:6333"` | Qdrant vector DB URL |
| `qdrant_api_key` | `None` | Optional for remote Qdrant |
| `sqlite_database_url` | `"sqlite:///./kisanvoice.db"` | SQLite path |

---

### 🌐 API Base URLs

| Field | Default | Description |
|---|---|---|
| `openweather_base_url` | `https://api.openweathermap.org/data/2.5` | OpenWeather |
| `groq_base_url` | `https://api.groq.com/openai/v1` | Groq |
| `elevenlabs_base_url` | `https://api.elevenlabs.io/v1` | ElevenLabs |

---

### 📱 WhatsApp / Twilio (Legacy)

| Field | Description |
|---|---|
| `twilio_account_sid` | Twilio SID (for legacy Twilio WhatsApp) |
| `twilio_auth_token` | Twilio auth token |
| `twilio_whatsapp_from` | Twilio sender number |

> These are **not used** by the active Meta WhatsApp integration (`ui/Meta_whatsapp.py`). They are leftovers from the older Twilio approach.

---

## Validation

Required API keys are validated on app startup. If a required key is missing or empty, the app raises a `ValueError` and refuses to start.

The validator allows **placeholder values** for development:
```python
# These pass validation (for testing without real keys):
GROQ_API_KEY=your_groq_api_key_here
ELEVENLABS_API_KEY=test_key_for_validation
```

---

## Example `.env` File

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxx
GOOGLE_IMAGE_KEYS=AIzaSy...key1,AIzaSy...key2
GOOGLE_STT_KEYS=AIzaSy...key1,AIzaSy...key2
ELEVENLABS_API_KEY=sk_xxxxxxxxxxxxx
OPENWEATHER_API_KEY=xxxxxxxxxxxxx

QDRANT_URL=http://localhost:6333
DEFAULT_LANGUAGE=kn
```

---

## Related Files

| File | Role |
|---|---|
| [`ADD_API_KEYS.md`](../../ADD_API_KEYS.md) | Guide on where to get each API key |
| [core/memory.py](memory.md) | Reads `qdrant_url` from settings |
| [services/groq_service.py](../services/groq_service.md) | Reads `groq_api_key` |
| [ui/Meta_whatsapp.py](../ui/Meta_whatsapp.md) | Reads Meta-specific vars directly from `os.getenv` |
