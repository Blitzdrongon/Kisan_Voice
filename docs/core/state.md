# 📄 `app/core/state.py` — Data Models & State Definitions

> **Back to:** [APP_DOCUMENTATION.md](../../APP_DOCUMENTATION.md)

---

## Overview

`state.py` defines the **core data models** used throughout the RaithaMithra application. It uses **Pydantic** for validation and provides enums, message types, conversation state containers, and a global in-memory state store.

---

## Enums

### `MessageType`

```python
class MessageType(str, Enum):
    TEXT    = "text"
    AUDIO   = "audio"
    IMAGE   = "image"
    WEATHER = "weather"
    SYSTEM  = "system"
```

Describes the type of content in a `Message`.

---

### `Language`

```python
class Language(str, Enum):
    KANNADA = "kn"
    ENGLISH = "en"
    HINDI   = "hi"
```

All three supported languages. Default across the app is `"kn"` (Kannada).

---

## Data Models

### `Message`

Represents a single message in a conversation.

| Field | Type | Description |
|---|---|---|
| `id` | `str` | Unique UUID |
| `type` | `MessageType` | text / audio / image / weather / system |
| `content` | `str` | The actual message text |
| `timestamp` | `datetime` | Auto-set to UTC now |
| `sender` | `str` | `"user"` or `"assistant"` |
| `metadata` | `dict` | Optional extra info |
| `language` | `Language` | Defaults to `Language.KANNADA` |

```python
# Example usage in conversation_nodes.py
message = Message(
    id=str(uuid.uuid4()),
    type=MessageType.TEXT,
    content="ಮಳೆ ಯಾವಾಗ?",
    sender="user",
    language=Language("kn")
)
```

---

### `ConversationState`

Represents the full state of an active conversation session.

| Field | Type | Description |
|---|---|---|
| `session_id` | `str` | Unique session identifier |
| `user_id` | `str` | User identifier |
| `messages` | `List[Message]` | All messages in this session |
| `current_language` | `Language` | Active language |
| `context` | `dict` | Arbitrary context key-value store |
| `created_at` | `datetime` | When session started |
| `updated_at` | `datetime` | Last update time |
| `last_weather_query` | `str` | Last weather query made |
| `weather_location` | `str` | Detected weather location |
| `voice_enabled` | `bool` | Whether voice output is active |
| `preferred_voice` | `str` | TTS voice preference |
| `whatsapp_number` | `str` | WhatsApp phone number if applicable |
| `whatsapp_session_active` | `bool` | Whether connected via WhatsApp |

> **Note:** `ConversationState` is the **Pydantic model** used in the `GlobalState` store. The **LangGraph workflow** uses a separate `WorkflowState` TypedDict defined in `workflow.py`.

---

### `UserProfile`

Persistent user profile data.

| Field | Type | Description |
|---|---|---|
| `user_id` | `str` | Unique identifier |
| `name` | `str` | Display name |
| `preferred_language` | `Language` | Defaults to Kannada |
| `location` | `str` | Optional location |
| `timezone` | `str` | Optional timezone |
| `created_at` | `datetime` | Profile creation time |
| `last_active` | `datetime` | Last activity time |
| `preferences` | `dict` | Flexible key-value preferences |

---

## `GlobalState`

An in-memory container holding all active conversations and user profiles for the running process.

```python
global_state = GlobalState()
```

| Method | Description |
|---|---|
| `get_conversation(session_id)` | Returns `ConversationState` or `None` |
| `create_conversation(session_id, user_id)` | Creates and stores a new `ConversationState` |
| `add_message(session_id, message)` | Appends a `Message` and updates `updated_at` |
| `get_user_profile(user_id)` | Returns `UserProfile` or `None` |
| `update_user_profile(user_id, **kwargs)` | Updates any field on the profile |

```python
# Example
from core.state import get_global_state

state = get_global_state()
conv = state.create_conversation("session_123", "user_456")
```

> ⚠️ `GlobalState` is **in-memory only**. Data is lost on server restart. Persistent storage is handled by the `MemoryManager` in `core/memory.py`.

---

## Global Accessor

```python
def get_global_state() -> GlobalState:
    return global_state
```

---

## Related Files

| File | Role |
|---|---|
| [core/memory.py](memory.md) | Persistent storage (SQLite + Qdrant) |
| [core/workflow.py](workflow.md) | Uses `WorkflowState` TypedDict (separate from these models) |
| [nodes/conversation_nodes.py](../nodes/conversation_nodes.md) | Creates `Message` objects per turn |
