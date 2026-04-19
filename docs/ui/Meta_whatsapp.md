# 📄 `app/ui/Meta_whatsapp.py` — Meta WhatsApp Cloud API Integration

> **Back to:** [APP_DOCUMENTATION.md](../../APP_DOCUMENTATION.md)

---

## Overview

`Meta_whatsapp.py` is a **standalone Flask application** that connects RaithaMithra to **WhatsApp via the Meta Cloud API** (previously known as "WhatsApp Business API"). It handles incoming messages via webhooks and sends responses back through the Graph API.

This is the **production WhatsApp integration** — use this over the older Twilio-based files.

---

## How to Run

```bash
cd app/ui
python Meta_whatsapp.py
# Starts Flask on 0.0.0.0:5000
```

For public access (development), use ngrok:
```bash
ngrok http 5000
```
Then register `https://<your-ngrok-id>.ngrok.io/webhook` in the Meta Developer Console.

---

## Required Environment Variables

Set these in your `.env` file:

| Variable | Description | Where to get it |
|---|---|---|
| `WHATSAPP_TOKEN` | Meta permanent access token | Meta Developer Console → App → WhatsApp → Config |
| `PHONE_NUMBER_ID` | Your WhatsApp business phone number ID | Meta Developer Console |
| `VERIFY_TOKEN` | Your custom secret for webhook verification | You set this yourself |
| `PUBLIC_BASE_URL` | Public HTTPS URL of this server | Your server URL or ngrok URL |
| `GRAPH_API_VERSION` | API version (default: `v17.0`) | Optional override |

---

## Flask Routes

### `GET /webhook` — Webhook Verification

Used by Meta to verify your webhook during setup.

```
Meta sends: ?hub.mode=subscribe&hub.verify_token=<your_token>&hub.challenge=<number>
```

If `hub.verify_token` matches `VERIFY_TOKEN` → returns `hub.challenge` (200 OK).  
Otherwise → returns 403 Forbidden.

---

### `POST /webhook` — Incoming Messages

Meta calls this for every incoming WhatsApp message.

**Flow:**

```
POST /webhook → parse JSON payload
    ↓
For each message in payload:
    │
    ├── type: "text"
    │       └── extract text body
    │
    ├── type: "image"
    │       ├── get media_id from payload
    │       ├── download_media_from_meta(media_id) → saves to downloads/images/
    │       └── set image_path
    │
    ├── type: "audio" / "voice" / "document"
    │       ├── get media_id
    │       ├── download_media_from_meta(media_id) → saves to downloads/audio/
    │       └── set audio_path
    │
    └── Launch threading.Thread(call_workflow_and_respond)
            (returns 200 immediately; processing continues in background)
```

Returns `"EVENT_RECEIVED", 200` immediately so Meta doesn't retry.

---

### `GET /uploads/<filename>` — Serve Audio Files

Publicly serves generated TTS audio files so WhatsApp can fetch them via URL.

```
GET /uploads/20240416_123456_response_abc123.mp3
```

Returns the audio file for WhatsApp to play.

---

### `GET /health` — Health Check

Returns current server status as JSON:

```json
{
    "ok": true,
    "time": "2024-04-16T12:34:56",
    "active_sessions": 3,
    "public_base_url_set": true,
    "phone_number_id_set": true
}
```

---

## Core Functions

### `call_workflow_and_respond(sender, user_input, image_path, audio_path)`

Runs in a **background thread** (so the webhook can return 200 immediately).

**Steps:**
1. Initializes workflow via `get_workflow()`.
2. Gets or creates user session in `user_sessions` dict.
3. Detects language from `user_input`.
4. Runs `asyncio.run(run_workflow_async(...))` — bridges sync thread + async workflow.
5. Sends text reply via `send_text_message(sender, text_reply)`.
6. If audio was generated:
   - Copies audio file → `uploads/` directory.
   - Builds public URL: `{PUBLIC_BASE_URL}/uploads/{filename}`.
   - Sends via `send_audio_via_link(sender, public_url)`.

---

### `download_media_from_meta(media_id, save_folder, suggested_ext) → str | None`

Downloads media (image/audio) from Meta's servers.

**Steps:**
1. GETs metadata from `https://graph.facebook.com/v17.0/{media_id}` → gets `url` + `mime_type`.
2. Downloads binary content from `url` using bearer token.
3. Saves to `save_folder/` with timestamped filename.
4. Returns the local file path.

---

### `send_text_message(to_number, text) → bool`

POSTs to the Graph API to send a WhatsApp text message:

```json
{
    "messaging_product": "whatsapp",
    "to": "+91XXXXXXXXXX",
    "type": "text",
    "text": {"body": "ನಿಮ್ಮ ಪ್ರಶ್ನೆಗೆ ಉತ್ತರ..."}
}
```

---

### `send_audio_via_link(to_number, audio_url, caption) → bool`

POSTs to the Graph API to send an audio message via a public URL:

```json
{
    "messaging_product": "whatsapp",
    "to": "+91XXXXXXXXXX",
    "type": "audio",
    "audio": {"link": "https://yourserver.com/uploads/response_abc.mp3"}
}
```

> ⚠️ WhatsApp requires audio to be served over **HTTPS** with a valid certificate. Ngrok provides this automatically for development.

---

## Session Management

```python
user_sessions: Dict[str, Dict[str, Any]] = {}
```

Keyed by sender phone number. Each session:
```python
{
    "session_id": "whatsapp_+91XXXXXXXXXX_20240416_123456",
    "user_id": "+91XXXXXXXXXX",
    "language": "kn",
    "created_at": "...",
    "conversation_history": [...]
}
```

> ⚠️ Sessions are **in-memory only** — reset when the Flask server restarts.

---

## `detect_language(text) → str`

Simple Kannada character detection:
```python
kannada_chars = set('ಅಆಇಈ...')
if any(char in kannada_chars for char in text):
    return "kn"
return "en"
```

---

## Directory Structure

```
app/ui/
├── downloads/
│   ├── images/   ← Images sent by WhatsApp users
│   └── audio/    ← Audio/voice messages from users
└── uploads/      ← TTS audio generated for users (publicly served)
```

---

## Complete Message Flow Diagram

```
WhatsApp User
    │ sends message (text / image / voice)
    ▼
Meta Cloud API
    │ POST /webhook
    ▼
Flask App (this file)
    │ parse payload
    │ download media if any
    │ threading.Thread →
    ▼
call_workflow_and_respond()
    │ asyncio.run(workflow.run_conversation())
    ▼
LangGraph Pipeline (core/workflow.py)
    │ → text response + optional audio file
    ▼
send_text_message(sender, reply)
    │ POST graph.facebook.com → sends text
    │
    └── if audio:
        copy audio → uploads/
        build public URL
        send_audio_via_link(sender, url)
        POST graph.facebook.com → sends audio
```

---

## Troubleshooting

| Problem | Likely Cause | Fix |
|---|---|---|
| Webhook verification fails | `VERIFY_TOKEN` mismatch | Match token in Meta Console with `.env` |
| Messages not received | Server not public | Use ngrok and update webhook URL in Meta Console |
| Audio not playing | `PUBLIC_BASE_URL` not set / not HTTPS | Set correct public URL |
| "Bot error" reply | Workflow import failed | Check logs for import errors in `core/` |
| Media download fails | `WHATSAPP_TOKEN` expired | Refresh token in Meta Developer Console |

---

## Related Files

| File | Role |
|---|---|
| [core/workflow.py](../core/workflow.md) | The pipeline called for every message |
| [services/elevenlabs_service.py](../services/elevenlabs_service.md) | Audio generated and linked here |
| `app/ui/README_WHATSAPP_INTEGRATION.md` | Additional WhatsApp setup notes |
| `ADD_API_KEYS.md` | Guide for getting WhatsApp tokens |
