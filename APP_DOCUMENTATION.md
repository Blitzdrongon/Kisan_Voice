# 📂 KisanVoice — `app/` Folder Documentation

> **Purpose:** This document explains the full architecture, folder structure, workflow logic, Meta WhatsApp integration, and all services inside the `app/` folder. Written for co-workers who are new to the project.

---

## 🌾 What is KisanVoice?

**KisanVoice** (ರೈತಮಿತ್ರ — "Farmer's Friend") is an AI-powered agricultural assistant designed to help farmers primarily in North Karnataka, India.

It accepts inputs in **Kannada, Hindi, or English** and can respond via:
- Text conversation (Chainlit web UI)
- Voice (speech-to-text and text-to-speech)
- Image analysis (disease detection, plant identification)
- WhatsApp (via Meta Cloud API)
- Weather forecast lookup

---

## 📚 Individual File Documentation

Click any file below to read its full dedicated documentation:

### Entry Points
| File | Description |
|---|---|
| [app/main.py](docs/main.md) | 🟢 **Production** Chainlit web UI — full LangGraph pipeline |
| [app/main_simple.py](docs/main_simple.md) | 🟡 **Demo** Chainlit UI — no API keys, keyword replies only |

### `core/` — Core Logic
| File | Description |
|---|---|
| [core/config.py](docs/core/config.md) | All settings & API key management (Pydantic BaseSettings) |
| [core/state.py](docs/core/state.md) | Data models: Message, Language, ConversationState, UserProfile |
| [core/memory.py](docs/core/memory.md) | Two-tier memory: SQLite (short-term) + Qdrant (long-term) |
| [core/workflow.py](docs/core/workflow.md) | LangGraph conversation pipeline — 4-node graph |

### `nodes/` — Pipeline Steps
| File | Description |
|---|---|
| [nodes/conversation_nodes.py](docs/nodes/conversation_nodes.md) | All 4 node functions: process, respond, save memory, generate audio |

### `services/` — External API Services
| File | Status | Description |
|---|---|---|
| [services/groq_service.py](docs/services/groq_service.md) | ✅ Active | Groq LLM + Whisper STT + Vision |
| [services/gemini_tts_service.py](docs/services/gemini_tts_service.md) | ⚠️ Initialized, not active | Gemini Flash TTS with key rotation |
| [services/gemini_stt_service.py](docs/services/gemini_stt_service.md) | ✅ Active | Gemini Flash STT via Files API |
| [services/elevenlabs_service.py](docs/services/elevenlabs_service.md) | ✅ **Active TTS** | ElevenLabs `eleven_v3` text-to-speech |
| [services/weather_service.py](docs/services/weather_service.md) | ✅ Active | OpenWeather current + 5-day forecast |
| [services/image_anylsis.py](docs/services/image_analysis.md) | ✅ Active | Gemini vision: disease / ID / describe |
| [services/whisper_services.py](docs/services/whisper_services.md) | ✅ Active | Groq Whisper STT (large-v3-turbo) |
| [services/rag_e5_groq.py](docs/services/rag_e5_groq.md) | ❌ Disabled | E5 embeddings + ChromaDB + Groq RAG |
| [services/gemma_with_RAG_services.py](docs/services/gemma_with_rag_services.md) | ❌ Disabled | Local Gemma 3 model + ChromaDB RAG |

### `prompt/`
| File | Description |
|---|---|
| [prompt/prompts.py](docs/prompt/prompts.md) | System prompt templates (imported but inline prompts used instead) |

### `ui/` — WhatsApp Integration
| File | Status | Description |
|---|---|---|
| [ui/Meta_whatsapp.py](docs/ui/Meta_whatsapp.md) | ✅ **Production** | Meta WhatsApp Cloud API — Flask webhook app |

---

## 📁 `app/` Folder Structure

```
app/
├── main.py                     # Chainlit web UI entry point
├── main_simple.py              # Simpler/backup Chainlit entry point
├── __init__.py
│
├── core/                       # Core logic (config, memory, state, workflow)
│   ├── config.py               # All app settings & API key management
│   ├── memory.py               # Short-term (SQLite) + Long-term (Qdrant) memory
│   ├── state.py                # Data models for messages, conversations, users
│   └── workflow.py             # LangGraph conversation pipeline
│
├── nodes/
│   └── conversation_nodes.py   # LangGraph node functions (pipeline steps)
│
├── services/                   # External API service wrappers
│   ├── groq_service.py         # Groq LLM + audio transcription (Whisper)
│   ├── gemini_tts_service.py   # Gemini Flash TTS (text → audio)
│   ├── gemini_stt_service.py   # Gemini Flash STT (audio → text)
│   ├── elevenlabs_service.py   # ElevenLabs TTS (alternative)
│   ├── weather_service.py      # OpenWeather API
│   ├── image_anylsis.py        # Gemini image analysis (disease / ID / describe)
│   ├── whisper_services.py     # Groq Whisper STT wrapper
│   ├── groq_service.py         # Groq LLM
│   ├── rag_e5_groq.py          # RAG service (E5 embeddings + Groq)
│   └── gemma_with_RAG_services.py  # Gemma RAG service (experimental)
│
├── prompt/
│   └── prompts.py              # System prompt templates
│
├── ui/                         # WhatsApp integration layer
│   ├── Meta_whatsapp.py        # Meta WhatsApp Cloud API (Flask app) ← MAIN
│   ├── whatsapp.py             # Twilio-based WhatsApp (older)
│   ├── whatsapp_new.py         # Newer Twilio version
│   ├── whatsapp_refactored.py  # Refactored Twilio version
│   ├── meta_whatsapp_refactored.py  # Another Meta API version
│   └── README_WHATSAPP_INTEGRATION.md
│
├── data/                       # Runtime data folder
├── logs/                       # Log files
├── uploads/                    # Generated audio files served publicly
└── test_files/                 # Test audio/image files
```

---

## 🔄 How the Conversation Workflow Works

The brain of KisanVoice is a **LangGraph pipeline** defined in `core/workflow.py`. Every message (text, voice, or image) from any channel flows through this same pipeline.

### Pipeline Diagram

```
User Input (Text / Audio / Image)
         │
         ▼
┌─────────────────┐
│  process_input  │  → Classify intent, load memory & user preferences
└────────┬────────┘
         │
         ▼
┌──────────────────┐
│ generate_response │  → Route to handler, call Groq LLM, build response
└────────┬─────────┘
         │
         ▼
┌───────────────────┐
│  save_to_memory   │  → Persist conversation to SQLite + Qdrant
└────────┬──────────┘
         │
         ▼
┌──────────────────────┐
│  generate_audio      │  → Convert text response to audio (ElevenLabs/Gemini)
└────────┬─────────────┘
         │
         ▼
    Response returned
  (text + optional audio file path)
```

---

## 🧠 `core/` — Core Logic

### `config.py` — Settings

All configuration is managed via **Pydantic BaseSettings**, reading from `.env`.

| Setting | Description |
|---|---|
| `GROQ_API_KEY` | Groq LLM & Whisper STT |
| `GOOGLE_IMAGE_KEYS` | Comma-separated Gemini keys for image analysis |
| `GOOGLE_STT_KEYS` | Comma-separated Gemini keys for TTS (and STT via same pool) |
| `ELEVENLABS_API_KEY` | ElevenLabs TTS |
| `OPENWEATHER_API_KEY` | Weather data |
| `QDRANT_URL` | Vector DB for long-term memory (default: localhost:6333) |
| `SQLITE_DATABASE_URL` | Short-term conversation memory |

> **Note:** Multiple Google API keys are supported for load balancing. If one key hits quota, the system automatically rotates to the next.

---

### `state.py` — Data Models

Defines the data structures used throughout the application:

| Class | Purpose |
|---|---|
| `Message` | A single text/audio/image message (has sender, language, content, timestamp) |
| `MessageType` | Enum: `text`, `audio`, `image`, `weather`, `system` |
| `Language` | Enum: `kn` (Kannada), `en` (English), `hi` (Hindi) |
| `ConversationState` | Full state of an ongoing chat session |
| `UserProfile` | User preferences (language, location, timezone) |
| `GlobalState` | In-memory store of all active conversations and users |

The **WorkflowState** (TypedDict in `workflow.py`) is what actually flows through the LangGraph pipeline:

```python
{
  "user_input": str,
  "session_id": str,
  "user_id": str,
  "language": str,            # "kn", "en", or "hi"
  "image_url": str | None,
  "audio_url": str | None,
  "messages": list,
  "current_intent": str,      # "weather", "image_analysis", "voice_request", "memory_query", "general"
  "assistant_response": str,
  "audio_response_path": str,
  "audio_generated": bool,
  "memory_saved": bool,
  ...
}
```

---

### `memory.py` — Memory System

KisanVoice has a **two-tier memory architecture**:

#### 1. Short-Term Memory (`ShortTermMemory`) — SQLite

Stores recent conversations in a local SQLite database. Three tables:

| Table | What it stores |
|---|---|
| `conversations` | Every Q&A exchange: user message, AI response, language, timestamp |
| `user_sessions` | Session creation time, last active, metadata |
| `user_preferences` | Language, voice_enabled, preferred_voice, location, timezone |

Used to build **context** for each conversation turn (last 5 exchanges shown to LLM).

#### 2. Long-Term Memory (`LongTermMemory`) — Qdrant

A vector database that stores conversation embeddings for **semantic search**.

- If Qdrant is not running, the system falls back to SQLite-only mode gracefully.
- Currently uses placeholder embeddings; real semantic search can be enabled by connecting an embedding service.

#### `MemoryManager`

The public interface that combines both:
```python
memory_manager.add_conversation(...)       # saves to SQLite + Qdrant
memory_manager.get_conversation_history(session_id)  # retrieves from SQLite
memory_manager.get_user_preferences(user_id)
memory_manager.search_memories(query)     # semantic search via Qdrant
```

---

### `workflow.py` — LangGraph Pipeline

`KisanVoiceWorkflow` builds and runs the 4-step LangGraph graph.

#### Key method: `run_conversation()`

```python
await workflow.run_conversation(
    user_input="ಮಳೆ ಯಾವಾಗ?",
    session_id="session_...",
    user_id="user123",
    language="kn",
    image_url=None,         # path to image file (optional)
    audio_url=None          # path to audio file (optional)
)
```

Returns a dict with:
- `assistant_response` — the text reply
- `audio_path` — path to generated audio file (or None)
- `audio_generated` — bool
- `intent` — detected intent
- `memory_saved` — bool

**Fallback mode:** If LangGraph fails to compile, the workflow runs the 4 node functions sequentially as plain Python calls (`_run_direct_conversation`).

---

## 🔗 `nodes/conversation_nodes.py` — Pipeline Steps

Each node is an `async` function that receives the full state dict and returns an updated state dict.

### Node 1: `process_user_input(state)`

1. Creates a `Message` object for the user input.
2. Loads the last 5 conversation turns from SQLite memory for context.
3. Loads user preferences (language override if set).
4. Calls `_classify_intent()` using keyword matching.

**Intent classification logic:**

| Intent | Triggers |
|---|---|
| `weather` | Keywords: ಮಳೆ, ಹವಾಮಾನ, rain, weather, temperature, hot, cold |
| `image_analysis` | Image URL present, or keywords: ಚಿತ್ರ, image, photo, picture |
| `voice_request` | Audio URL present, or keywords: ಧ್ವನಿ, voice, audio, speak |
| `memory_query` | Keywords: ನೆನಪು, ಮೊದಲು, memory, remember, previous |
| `general` | Everything else |

---

### Node 2: `generate_response(state)`

Routes to the correct handler based on intent:

| Intent | Handler | What it does |
|---|---|---|
| `weather` | `_handle_weather_query()` | Calls OpenWeather API for Hubli, returns temp + description |
| `image_analysis` | `_handle_image_analysis()` | Sends image to `image_anylsis` service via Gemini |
| `voice_request` | `_handle_voice_request()` | If audio present, calls Gemini STT → routes through general handler |
| `memory_query` | `_handle_memory_query()` | Returns a message about conversation history |
| `general` | `_handle_general_conversation()` | Calls Groq LLM with system prompt + context |

---

### Node 3: `save_to_memory(state)`

Saves the completed exchange (`user_input` + `assistant_response`) to the `MemoryManager`.

---

### Node 4: `generate_audio_response(state)`

Converts the text response to audio using **ElevenLabs** TTS:
- Generates an `.mp3` file.
- Saves it to `app/uploads/`.
- Sets `audio_response_path` and `audio_generated: True` in state.

> Currently wired to ElevenLabs. `GeminiTTSService` is also available as an alternative (see services).

---

## ⚙️ `services/` — External Service Wrappers

### `groq_service.py` — Groq LLM & Whisper

**Primary AI engine.** Handles:

1. **Text generation** (`generate_text()`) — Uses `llama-3.3-70b-versatile` by default.
   - System prompt: "KISAN VOICE" — agriculture expert for Karnataka farmers.
   - Answers in the detected language only.
   - Focuses on crops: Jowar, Bajra, Cotton, Tur, Groundnut, Maize, Paddy, Onion, Sugarcane.

2. **Audio transcription** (`transcribe_audio()`) — Uses `whisper-1` model via Groq.

3. **Image analysis** (`analyze_image()`) — Uses `llama-3.2-90b-vision-preview` with base64-encoded images.

```python
# Example Groq LLM call
response = await groq_service.generate_text(
    prompt="ಹತ್ತಿ ಬೆಳೆಯಲ್ಲಿ ಕೀಟ ನಿರ್ವಹಣೆ ಹೇಗೆ?",
    language="kn",
    context="User location: Hubli\nPrevious: ..."
)
```

---

### `gemini_tts_service.py` — Gemini Text-to-Speech

Uses **Gemini 2.5 Flash TTS** (`gemini-2.5-flash-preview-tts`) to generate audio.

- Supports multiple API keys with **round-robin load balancing**.
- Returns raw WAV bytes (PCM → WAV).
- Voice: `"Puck"` (default Gemini voice).

```python
audio_bytes = await gemini_tts_service.text_to_speech(text="ನಮಸ್ಕಾರ", language="kn")
gemini_tts_service.save_audio_to_file(audio_bytes, "output.wav")
```

---

### `gemini_stt_service.py` — Gemini Speech-to-Text

Uses **Gemini 2.5 Flash** to transcribe uploaded audio files.

- Supports multiple API keys with **round-robin load balancing** via `GeminiKeyBalancer`.
- Uploads audio via the Gemini Files API.
- Handles formats: `.mp3`, `.wav`, `.ogg`, `.flac`, `.aac`, `.aiff`.
- Strict prompt: "Transcribe EXACTLY as spoken. Do NOT translate."

```python
transcription = await gemini_stt_service.transcribe("/path/to/audio.wav", language="kn")
```

---

### `elevenlabs_service.py` — ElevenLabs TTS

Alternative TTS engine using **ElevenLabs `eleven_v3` model**.

- If language is Kannada (`kn`), it tries to find an Indian accent voice.
- Also supports **streaming** TTS via `text_to_speech_stream()`.
- Returns MP3 bytes.

> **Current usage:** This is the **active TTS** called in `generate_audio_response()` in the pipeline. GeminiTTS is available but not yet wired as default.

---

### `weather_service.py` — OpenWeather API

Fetches current weather and 5-day forecasts from OpenWeatherMap.

- Default city: **Hubli, India**.
- Translates common weather descriptions to Kannada (e.g., "light rain" → "ಸ್ವಲ್ಪ ಮಳೆ").
- Returns structured data: temperature, humidity, pressure, wind speed, description.

```python
weather = await weather_service.get_current_weather(city="Hubli", country_code="IN", language="kn")
# Returns: {"city": "Hubli", "temperature": {"current": 32.1}, "description": "ಸ್ಪಷ್ಟ ಆಕಾಶ", ...}
```

---

### `image_anylsis.py` — Gemini Image Analysis

Uses **Gemini 2.5 Flash** vision model. Supports multiple API keys with load balancing.

**3-step analysis process:**

```
Image Input
    │
    ▼
classify_image()     → "disease" | "identification" | "none"
    │
    ├─ disease      → disease_analysis()    → disease name, affected crop, symptoms, treatment, prevention, severity
    ├─ identification → identification_image() → common name, scientific name, family, uses, native region
    └─ none         → describe_image()      → general image description
```

All responses respect the detected language (`kn` / `en` / `hi`).

---

## 📱 `ui/Meta_whatsapp.py` — WhatsApp Cloud API Integration

This is the **production WhatsApp integration** using **Meta's WhatsApp Cloud API** (not Twilio). It's a standalone Flask application.

### How It Works

```
WhatsApp User sends message
         │
         ▼
Meta Cloud API → POST /webhook  (Flask endpoint)
         │
         ▼
Webhook parses message type:
  - text    → extract text body
  - image   → download image via Graph API → save to downloads/images/
  - audio/voice → download audio via Graph API → save to downloads/audio/
         │
         ▼
threading.Thread → call_workflow_and_respond()
  (runs in background so webhook returns 200 immediately)
         │
         ▼
  asyncio.run(workflow.run_conversation(...))
         │
    ┌────┴───────────────────────────────┐
    │                                    │
    ▼                                    ▼
send_text_message(sender, reply)    if audio_generated:
                                      copy audio → uploads/
                                      build public URL
                                      send_audio_via_link(sender, url)
```

### Required Environment Variables

| Variable | Description |
|---|---|
| `WHATSAPP_TOKEN` | Meta permanent access token (from Facebook Developer Console) |
| `PHONE_NUMBER_ID` | Your WhatsApp business phone number ID |
| `VERIFY_TOKEN` | Your custom webhook verification secret |
| `PUBLIC_BASE_URL` | Public HTTPS URL of this server (e.g., ngrok URL or your server) |
| `GRAPH_API_VERSION` | Meta Graph API version (default: `v17.0`) |

### Flask Routes

| Route | Method | Description |
|---|---|---|
| `/webhook` | GET | Meta webhook verification (hub challenge handshake) |
| `/webhook` | POST | Incoming WhatsApp messages |
| `/uploads/<filename>` | GET | Serves generated audio files publicly for WhatsApp |
| `/health` | GET | Health check — returns active session count, config status |

### Folder Layout (inside `app/ui/`)

```
ui/
├── downloads/
│   ├── images/   ← Downloaded images from WhatsApp users
│   └── audio/    ← Downloaded audio messages from WhatsApp users
└── uploads/      ← Generated TTS audio files served to WhatsApp users
```

### Starting the WhatsApp Bot

```bash
cd app/ui
python Meta_whatsapp.py
# Runs Flask on 0.0.0.0:5000
```

> For local development, expose port 5000 publicly using **ngrok**:
> ```bash
> ngrok http 5000
> ```
> Then set `PUBLIC_BASE_URL=https://<your-ngrok-id>.ngrok.io` in your `.env`.

---

## 🖥️ `main.py` — Chainlit Web Chat UI

The Chainlit web interface provides a browser-based chat with voice input.

### Session Lifecycle

| Hook | What happens |
|---|---|
| `@cl.on_chat_start` | Creates session, sends bilingual welcome message (Kannada + English) |
| `@cl.on_message` | Receives text/audio/image, runs workflow, sends text + audio reply |
| `@cl.on_chat_end` | Cleans up session from memory |

### Message Handling Flow

```python
# 1. Audio input → transcribe via Groq Whisper → use as text
# 2. Image input → save to uploads/ + add description to prompt
# 3. Detect language (Kannada chars check)
# 4. Run workflow.run_conversation()
# 5. Send text response
# 6. If audio_path exists → send cl.Audio element (auto-play)
```

---

## 🗣️ Language Detection

Language is detected in two places:

1. **Simple char-set check** (in `main.py` and `Meta_whatsapp.py`):
   - Checks if input contains Kannada Unicode characters.
   - If yes → `"kn"`, else → `"en"`.

2. **Full Unicode detection** (`detect_language()` in `conversation_nodes.py`):
   - Also detects Hindi/Devanagari characters → `"hi"`.
   - Falls back to `"en"`.

---

## 🔑 API Keys Summary

| Service | Key Variable | Used For |
|---|---|---|
| Groq | `GROQ_API_KEY` | LLM (text generation) + Whisper STT |
| Google Gemini | `GOOGLE_IMAGE_KEYS` | Image analysis (vision model) |
| Google Gemini | `GOOGLE_STT_KEYS` | TTS (Gemini Flash TTS) |
| ElevenLabs | `ELEVENLABS_API_KEY` | Text-to-Speech (active TTS) |
| OpenWeatherMap | `OPENWEATHER_API_KEY` | Weather data |
| Meta | `WHATSAPP_TOKEN` | WhatsApp send/receive |
| Meta | `PHONE_NUMBER_ID` | WhatsApp sender number |

> Multiple Google API keys can be provided as comma-separated values for automatic load-balancing between keys.  
> Example: `GOOGLE_IMAGE_KEYS=AIza...key1,AIza...key2,AIza...key3`

---

## 🚦 Known States & Fallbacks

| Situation | Fallback Behavior |
|---|---|
| Groq LLM fails | Returns "ಕ್ಷಮಿಸಿ, ಒಂದು ದೋಷ ಸಂಭವಿಸಿದೆ." (Kannada) or "Sorry, an error occurred." |
| LangGraph fails to compile | Falls back to `_run_direct_conversation()` (sequential node calls) |
| Qdrant not running | MemoryManager uses SQLite only (no semantic search) |
| ElevenLabs TTS fails | `audio_generated = False`; only text reply is sent |
| Gemini key quota exceeded | Rotates to next key; raises RuntimeError if all keys exhausted |
| Audio transcription fails | Returns error message, asks user to type instead |
| WhatsApp media download fails | Logs error, continues with empty text body |

---

## 📋 Quick Reference: Adding a New Service

1. Create `app/services/my_service.py` following the pattern:
   ```python
   class MyService:
       def __init__(self): ...
   
   my_service = MyService()
   
   def get_my_service() -> MyService:
       return my_service
   ```

2. Import it in `nodes/conversation_nodes.py`:
   ```python
   from services.my_service import get_my_service
   self.my_service = get_my_service()
   ```

3. Add a new intent in `_classify_intent()` and a handler in `generate_response()`.

---

## 📋 Quick Reference: Adding a New Intent

1. Add keywords in `_classify_intent()` in `conversation_nodes.py`
2. Add an `elif intent == "my_intent":` branch in `generate_response()`
3. Create a `_handle_my_intent()` async method
4. Test via Chainlit UI or WhatsApp

---

*Last updated: April 2026 | KisanVoice v1.0*
