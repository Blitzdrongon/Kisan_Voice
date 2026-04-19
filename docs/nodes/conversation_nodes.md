# 📄 `app/nodes/conversation_nodes.py` — LangGraph Node Functions

> **Back to:** [APP_DOCUMENTATION.md](../../APP_DOCUMENTATION.md)

---

## Overview

`conversation_nodes.py` contains the `ConversationNodes` class which holds all **LangGraph node functions**. Every node receives the full `WorkflowState` dict, performs its work, and returns an updated state dict.

This is the **business logic hub** of RaithaMithra — intent classification, response routing, memory saving, and audio generation all happen here.

---

## Class: `ConversationNodes`

Initialized with all required services:

```python
self.groq_service        = get_groq_service()
self.weather_service     = get_weather_service()
self.elevenlabs_service  = get_elevenlabs_service()
self.memory_manager      = get_memory_manager()
self.image_analysis      = get_image_analysis()
self.whisper_service     = get_whisper_service()
self.gemini_tts_service  = get_gemini_tts_service()
self.gemini_stt_service  = get_gemini_stt_service()
```

---

## Node Functions

### Node 1: `process_user_input(state)`

**Purpose:** Parse the incoming message, classify intent, load memory context.

**Steps:**
1. Normalizes `state` to a plain dict (handles Pydantic objects).
2. Creates a `Message` object and appends it to `state["messages"]`.
3. Loads last 5 conversation turns from `memory_manager.get_conversation_history(session_id)`.
4. Loads `user_preferences` from memory; may override `language` if user has a saved preference.
5. Calls `_classify_intent()` to determine `current_intent`.

**State keys set:** `messages`, `conversation_history`, `user_preferences`, `current_intent`

---

### Node 2: `generate_response(state)`

**Purpose:** Generate the AI response based on the classified intent.

**Routing logic:**

```python
if intent == "weather":
    response = await _handle_weather_query(...)

elif intent == "image_analysis":
    response = await _handle_image_analysis(state, ...)

elif intent == "voice_request":
    response = await _handle_voice_request(..., audio_url=state["audio_url"])

elif intent == "memory_query":
    response = await _handle_memory_query(...)

else:  # "general"
    response = await _handle_general_conversation(...)
```

Creates an assistant `Message` and sets `state["assistant_response"]`.

---

### Node 3: `save_to_memory(state)`

**Purpose:** Persist the Q&A exchange to memory.

Calls:
```python
memory_id = self.memory_manager.add_conversation(
    session_id, user_id,
    user_message=state["user_input"],
    assistant_response=state["assistant_response"],
    language=state["language"],
    metadata={"intent": state["current_intent"], ...}
)
```

Sets `state["memory_saved"] = True` and `state["memory_id"] = memory_id`.

---

### Node 4: `generate_audio_response(state)`

**Purpose:** Convert the text response to speech and save the audio file.

**Steps:**
1. Waits 2 seconds (`time.sleep(2)`) — buffer for upstream processing.
2. Calls `self.elevenlabs_service.text_to_speech(text, language)`.
3. If audio returned → saves to `app/uploads/response_<uuid>.mp3`.
4. Sets `state["audio_response_path"]` and `state["audio_generated"] = True`.

> ⚠️ Currently uses **ElevenLabs** as the active TTS. `GeminiTTSService` is injected but not connected to this node.

---

## Private Handler Methods

### `_classify_intent(text, language, image_url, audio_url) → str`

Keyword-based intent classification:

| Intent | Triggers |
|---|---|
| `weather` | ಮಳೆ, ಹವಾಮಾನ, ತಾಪಮಾನ, rain, weather, temperature, hot, cold |
| `image_analysis` | `image_url` present, or: ಚಿತ್ರ, image, photo, picture, analyze, describe |
| `voice_request` | `audio_url` present, or: ಧ್ವನಿ, voice, audio, speak, sound |
| `memory_query` | ನೆನಪು, ಮೊದಲು, ಹಿಂದೆ, memory, remember, before, previous |
| `general` | Default (everything else) |

---

### `_build_context(user_input, conversation_history, user_preferences, language) → str`

Constructs the context string passed to the LLM:
- Appends user location if known.
- Appends preferred language.
- Appends last 3 exchanges as "Previous: Q → A" lines.
- Appends current query.

---

### `_handle_weather_query(query, language, context) → str`

- Calls `weather_service.get_current_weather(city="hubli", country_code="IN", language=language)`.
- Returns formatted weather string in Kannada or English.
- Default city is **Hubli** (hardcoded — future improvement: extract city from query using NER).

---

### `_handle_image_analysis(state, language, context) → str`

- Reads `image_path` from `state["image_url"]`.
- Calls `self.image_analysis.analyze_image(image_path, language=language)`.
- Returns the analysis string (disease / identification / description).

---

### `_handle_voice_request(query, language, context, audio_url) → str`

- If `audio_url` is provided: calls `gemini_stt_service.transcribe(audio_url, language)`.
- If transcription succeeds: routes to `_handle_general_conversation(transcription, ...)`.
- If no audio: returns a fallback message asking the user to send audio.

---

### `_handle_memory_query(query, language, context) → str`

Returns a static message inviting further questions about previous conversations. (Future: actual memory lookup via `memory_manager.search_memories()`.)

---

### `_handle_general_conversation(query, language, context) → str`

Calls `groq_service.generate_text(prompt=query, language=language, context=context)` and returns the result.

This is the **default handler** — all agricultural Q&A flows through here.

---

## `detect_language(text) → str` (static utility)

Full Unicode-based language detection. Checks against complete Kannada and Hindi/Devanagari character sets:

- Any Kannada char → `"kn"`
- Any Hindi/Devanagari char → `"hi"`
- Default → `"en"`

> This function exists in this file but is **currently not called** (commented out). Language is detected upstream in the UI entrypoints.

---

## Global Instance

```python
conversation_nodes = ConversationNodes()

def get_conversation_nodes() -> ConversationNodes:
    return conversation_nodes
```

---

## Related Files

| File | Role |
|---|---|
| [core/workflow.py](../core/workflow.md) | Registers these functions as LangGraph nodes |
| [services/groq_service.py](../services/groq_service.md) | Called by `_handle_general_conversation` |
| [services/gemini_stt_service.py](../services/gemini_stt_service.md) | Called by `_handle_voice_request` |
| [services/elevenlabs_service.py](../services/elevenlabs_service.md) | Called by `generate_audio_response` |
| [services/image_anylsis.py](../services/image_analysis.md) | Called by `_handle_image_analysis` |
| [services/weather_service.py](../services/weather_service.md) | Called by `_handle_weather_query` |
| [core/memory.py](../core/memory.md) | Called in `process_user_input` and `save_to_memory` |
