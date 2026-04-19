
 # 📄 `app/main_simple.py` — Demo / Testing Chainlit App

> **Back to:** [APP_DOCUMENTATION.md](../APP_DOCUMENTATION.md)

---

## Overview

`main_simple.py` is a **stripped-down demo version** of the Chainlit chat interface designed to run **without any API keys**. It provides hardcoded, keyword-based responses to simulate the real app for testing the UI, Chainlit setup, and session management.

> ⚠️ **This is NOT the production entry point.** Use `main.py` for production.

---

## When to Use This

- Testing that Chainlit is installed and running correctly.
- Demonstrating the UI without setting up API keys.
- Verifying the session management and message flow logic in isolation.

---

## How to Run

```bash
chainlit run app/main_simple.py
```

---

## Key Difference from `main.py`

`main_simple.py` has **no external service calls**. Instead of calling the workflow, it uses a local `generate_simple_response()` function:

```python
async def generate_simple_response(user_input, language, image_url):
    ...
    # Returns hardcoded responses based on keyword matching
```

| Keyword detected | Response |
|---|---|
| ಹಲೋ / hello / hi | "Hello! I am RaithaMithra..." |
| ಹವಾಮಾನ / weather | "For weather info, set up API keys." |
| ಬೆಳೆ / crop / pest | "For agricultural advice, set up API keys." |
| Image uploaded | "For image analysis, set up API keys." |
| Any other | Generic "add API keys" message |

Responses are language-aware (Kannada or English based on character detection).

---

## Session Management

Identical to `main.py`:
```python
user_sessions: Dict[str, Dict[str, Any]] = {}
```
- Keyed by Chainlit `user_id`.
- Tracks `session_id`, `language`, `conversation_history`.

---

## Audio Handling (Demo Mode)

When audio input is received:
- The audio element is echoed back to the user.
- **No real transcription** happens. A placeholder string is used:
  ```
  "[Voice input received - transcription would happen here with API keys]"
  ```
- This placeholder text is then passed to `generate_simple_response()`.

---

## Chainlit Hooks

| Hook | Behaviour |
|---|---|
| `@cl.on_chat_start` | Same welcome message as `main.py` + note that this is a demo version |
| `@cl.on_message` | Handles audio / image / text; calls `generate_simple_response()` |
| `@cl.on_chat_end` | Cleans up `user_sessions` |

---

## Related Files

| File | Role |
|---|---|
| [main.py](main.md) | Production version — use this instead |
| [core/workflow.py](core/workflow.md) | The real pipeline that `main.py` uses |
