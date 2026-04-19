# 📄 `app/core/memory.py` — Memory Management System

> **Back to:** [APP_DOCUMENTATION.md](../../APP_DOCUMENTATION.md)

---

## Overview

`memory.py` implements a **two-tier memory architecture** for KisanVoice:

| Tier | Storage | Purpose |
|---|---|---|
| Short-term | SQLite (local file) | Conversation history, user preferences, sessions |
| Long-term | Qdrant (vector DB) | Semantic search over past conversations |

The `MemoryManager` class provides a unified API that orchestrates both.

---

## Classes

### `MemoryItem` (dataclass)

A single item stored in memory.

| Field | Type | Description |
|---|---|---|
| `id` | `str` | UUID |
| `content` | `str` | Text content |
| `metadata` | `dict` | Extra info (session, intent, timestamp) |
| `embedding` | `List[float]` | Vector embedding (optional) |
| `timestamp` | `datetime` | Auto-set to UTC now |
| `memory_type` | `str` | `"conversation"`, `"knowledge"`, or `"experience"` |
| `language` | `str` | `"kn"`, `"en"`, `"hi"` |
| `tags` | `List[str]` | Optional tags |

---

### `ShortTermMemory`

SQLite-backed short-term memory. Database file: `app/data/kisanvoice.db`

#### Database Schema

**`conversations` table:**
```sql
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    user_message TEXT NOT NULL,
    assistant_response TEXT NOT NULL,
    language TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    metadata TEXT  -- JSON string
)
```

**`user_sessions` table:**
```sql
CREATE TABLE user_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    language TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    last_active DATETIME NOT NULL,
    metadata TEXT
)
```

**`user_preferences` table:**
```sql
CREATE TABLE user_preferences (
    user_id TEXT PRIMARY KEY,
    language TEXT NOT NULL,
    voice_enabled BOOLEAN DEFAULT 1,
    preferred_voice TEXT,
    location TEXT,
    timezone TEXT,
    updated_at DATETIME NOT NULL
)
```

#### Key Methods

| Method | Returns | Description |
|---|---|---|
| `add_conversation(session_id, user_id, user_message, assistant_response, language, metadata)` | `str` (UUID) | Inserts a Q&A exchange |
| `get_conversation_history(session_id, limit=10)` | `List[dict]` | Gets recent exchanges in chronological order |
| `get_user_preferences(user_id)` | `dict \| None` | Returns preference dict |
| `update_user_preferences(user_id, preferences)` | `bool` | Upserts preferences |

```python
# Example
history = short_term.get_conversation_history("session_123", limit=5)
# Returns last 5 exchanges in chronological order
```

---

### `LongTermMemory`

Qdrant-backed vector database for semantic memory search.

- Collection: `kisanvoice_memory`
- Vector size: 1536 dimensions
- Distance metric: Cosine similarity

> **Current state:** Fully implemented but using **placeholder embeddings** (zero vectors). Real semantic search requires connecting an embedding model (e.g., sentence-transformers or Google Embeddings API).

#### Key Methods

| Method | Returns | Description |
|---|---|---|
| `add_memory(content, metadata, embedding)` | `str \| None` | Stores content + vector in Qdrant |
| `search_memories(query, limit=5)` | `List[dict]` | Semantic search (returns `[]` until real embeddings enabled) |

#### Graceful Fallback

If Qdrant is not running:
```
WARNING: Qdrant not available at http://localhost:6333: ...
INFO: Continuing without Qdrant - using SQLite only
```
The app continues normally using SQLite only.

---

### `MemoryManager`

The **unified public interface** combining both memory tiers.

```python
from core.memory import get_memory_manager

memory = get_memory_manager()
```

#### Methods

```python
# Save an exchange (writes to SQLite + Qdrant)
memory_id = memory.add_conversation(
    session_id="session_123",
    user_id="user_456",
    user_message="ಹತ್ತಿ ಬೆಳೆಯಲ್ಲಿ ಕೀಟ ಏನು?",
    assistant_response="ಬೆಂಕಿ ರೋಗ ಇರಬಹುದು...",
    language="kn",
    metadata={"intent": "pest_disease"}
)

# Get conversation context (SQLite only)
history = memory.get_conversation_history("session_123", limit=5)

# Get user preferences
prefs = memory.get_user_preferences("user_456")

# Update preferences
memory.update_user_preferences("user_456", {"language": "kn", "location": "Hubli"})

# Semantic search (Qdrant - currently returns [] until embeddings configured)
results = memory.search_memories("cotton pest control")
```

---

## Data Flow in the Pipeline

```
Node 1: process_input
  → memory.get_conversation_history(session_id, limit=5)  ← provides context to LLM
  → memory.get_user_preferences(user_id)                  ← may override language

Node 3: save_to_memory
  → memory.add_conversation(...)                           ← persists the exchange
```

---

## Enabling Real Semantic Search

To enable Qdrant semantic search:

1. Start Qdrant locally: `docker run -p 6333:6333 qdrant/qdrant`
2. Integrate an embedding model to generate real vectors in `LongTermMemory.add_memory()`.
3. Implement the `search_memories()` query with a real embedding of the search query.

---

## Related Files

| File | Role |
|---|---|
| [core/config.py](config.md) | Provides `qdrant_url` and `sqlite_database_url` |
| [core/state.py](state.md) | Defines `MemoryItem` conceptually aligned models |
| [nodes/conversation_nodes.py](../nodes/conversation_nodes.md) | Calls `get_memory_manager()` in nodes |
