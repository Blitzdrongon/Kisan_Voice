# 📄 `app/core/workflow.py` — LangGraph Conversation Pipeline

> **Back to:** [APP_DOCUMENTATION.md](../../APP_DOCUMENTATION.md)

---

## Overview

`workflow.py` defines the **main conversation pipeline** for RaithaMithra using **LangGraph**. It orchestrates the 4-node graph that processes every message from any channel (Chainlit UI, WhatsApp).

---

## Class: `RaithaMithraWorkflow`

The single workflow class that builds and runs the LangGraph state machine.

```python
from core.workflow import get_workflow

workflow = get_workflow()
result = await workflow.run_conversation(...)
```

---

## `WorkflowState` (TypedDict)

The state dictionary that flows through all nodes:

| Key | Type | Description |
|---|---|---|
| `user_input` | `str` | The user's text (or transcription) |
| `session_id` | `str` | Session identifier |
| `user_id` | `str` | User identifier |
| `language` | `str` | `"kn"`, `"en"`, or `"hi"` |
| `image_url` | `str \| None` | Path to uploaded image file |
| `audio_url` | `str \| None` | Path to uploaded audio file |
| `messages` | `list` | All `Message` dicts this turn |
| `current_intent` | `str \| None` | Classified intent |
| `assistant_response` | `str \| None` | Generated text response |
| `audio_response_path` | `str \| None` | Path to generated audio file |
| `audio_generated` | `bool` | Whether audio was created |
| `conversation_history` | `list` | Past exchanges from memory |
| `user_preferences` | `dict` | User preference data |
| `memory_saved` | `bool` | Whether exchange was persisted |
| `memory_id` | `str \| None` | UUID of saved memory record |
| `error` | `str \| None` | Error string if any node failed |

---

## Pipeline Graph

```
process_input → generate_response → save_to_memory → generate_audio → END
```

Built with `StateGraph(WorkflowState)`:

```python
workflow.add_node("process_input",    self.nodes.process_user_input)
workflow.add_node("generate_response", self.nodes.generate_response)
workflow.add_node("save_to_memory",   self.nodes.save_to_memory)
workflow.add_node("generate_audio",   self.nodes.generate_audio_response)

workflow.add_edge("process_input",    "generate_response")
workflow.add_edge("generate_response","save_to_memory")
workflow.add_edge("save_to_memory",   "generate_audio")
workflow.add_edge("generate_audio",   END)

workflow.set_entry_point("process_input")
compiled = workflow.compile()
```

---

## `run_conversation()` — Main Entry Point

```python
async def run_conversation(
    self,
    user_input: str,
    session_id: str = None,
    user_id: str = None,
    language: str = "kn",
    image_url: str = None,
    audio_url: str = None
) -> Dict[str, Any]:
```

### Audio Pre-processing

If `audio_url` is provided and `user_input` is empty, the workflow **transcribes the audio first** using Whisper before running the pipeline:

```python
if audio_url and not user_input.strip():
    transcription = await whisper.transcribe_file(audio_url, language=language)
    user_input = transcription
```

### Returns

```python
{
    "assistant_response": str,       # Text reply
    "audio_path": str | None,        # Path to .mp3/.wav file
    "audio_generated": bool,
    "intent": str,                   # Detected intent
    "language": str,
    "memory_saved": bool,
    "memory_id": str | None,
    "messages": list,
    "conversation_history": list,
    "user_preferences": dict,
    "error": str | None
}
```

---

## Fallback Modes

### 1. `_build_simple_workflow()` — Simple Graph Fallback

If the full 4-node graph fails to compile (e.g., LangGraph version issue), a 2-node graph is attempted:

```
process_input → generate_response → END
```

Memory saving and audio generation are skipped.

### 2. `_run_direct_conversation()` — No-Graph Fallback

If both graph compilations fail, nodes are called sequentially as plain Python:

```python
state = await self.nodes.process_user_input(state)
state = await self.nodes.generate_response(state)
state = await self.nodes.save_to_memory(state)
state = await self.nodes.generate_audio_response(state)
```

This guarantees the app always responds regardless of LangGraph availability.

---

## LangGraph Import Compatibility

The module handles multiple LangGraph versions gracefully:

```python
try:
    from langgraph import StateGraph, END
except ImportError:
    try:
        from langgraph.graph import StateGraph, END
    except ImportError:
        # ... further fallbacks
```

---

## Global Instance

```python
raithamithra_workflow = RaithaMithraWorkflow()

def get_workflow() -> RaithaMithraWorkflow:
    return raithamithra_workflow
```

A single workflow instance is created at module load time and shared across all sessions.

---

## `get_workflow_info()` — Diagnostic

Returns a dict describing the current workflow state:

```python
{
    "name": "RaithaMithra Conversation Workflow",
    "nodes": ["process_input", "generate_response", "save_to_memory", "generate_audio"],
    "entry_point": "process_input",
    "end_point": "END",
    "status": "active"  # or "fallback_mode"
}
```

---

## Related Files

| File | Role |
|---|---|
| [nodes/conversation_nodes.py](../nodes/conversation_nodes.md) | The 4 node functions executed in this graph |
| [core/state.py](state.md) | Defines `ConversationState` and `WorkflowState` |
| [services/whisper_services.py](../services/whisper_services.md) | Called here for audio pre-transcription |
| [main.py](../main.md) | Calls `workflow.run_conversation()` per chat message |
| [ui/Meta_whatsapp.py](../ui/Meta_whatsapp.md) | Also calls `workflow.run_conversation()` per WhatsApp message |
