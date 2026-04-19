#!/usr/bin/env python3
"""
meta_whatsapp_app.py

Single-file Flask app implementing WhatsApp Cloud API webhook + A1 audio-serving approach.

Requirements:
  pip install flask python-dotenv requests loguru

Environment variables:
  WHATSAPP_TOKEN, PHONE_NUMBER_ID, VERIFY_TOKEN, PUBLIC_BASE_URL

Place this file in your project root where `core` package is importable (same as earlier Twilio app).
"""
import os
import io
import json
import threading
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
import requests
from loguru import logger

# Load .env
load_dotenv()

# --- Config ------------------------------------------------------------
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")

GRAPH_API_VERSION = os.getenv("GRAPH_API_VERSION", "v17.0")
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

if not WHATSAPP_TOKEN:
    logger.warning("WHATSAPP_TOKEN not set. Outbound message sending will fail until provided.")
if not PHONE_NUMBER_ID:
    logger.warning("PHONE_NUMBER_ID not set. Outbound message sending will fail until provided.")
if not VERIFY_TOKEN:
    logger.warning("VERIFY_TOKEN not set. Webhook verification may fail.")
if not PUBLIC_BASE_URL:
    logger.warning("PUBLIC_BASE_URL not set. Generated audio links will not be publicly accessible.")

# --- Imports from your project -----------------------------------------
import sys
THIS_DIR = Path(__file__).resolve().parent
sys.path.append(str(THIS_DIR))
sys.path.append(str(THIS_DIR.parent))

try:
    from core.workflow import get_workflow
except Exception as e:
    logger.error(f"Could not import get_workflow(): {e}")
    raise

# --- Directories -------------------------------------------------------
BASE_DIR = THIS_DIR
DOWNLOADS_DIR = (BASE_DIR / "downloads")
IMAGES_DIR = DOWNLOADS_DIR / "images"
AUDIO_IN_DIR = DOWNLOADS_DIR / "audio"
UPLOADS_DIR = (BASE_DIR / "uploads")

for d in (IMAGES_DIR, AUDIO_IN_DIR, UPLOADS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# --- Flask app ---------------------------------------------------------
app = Flask(__name__)

# Session store (in-memory)
user_sessions: Dict[str, Dict[str, Any]] = {}

# --- Utilities ---------------------------------------------------------
def _safe_ext_from_mimetype(mime_type: Optional[str]) -> str:
    if not mime_type:
        return "bin"
    ext = mime_type.split("/")[-1].split(";")[0].lower()
    return "jpg" if ext == "jpeg" else ext

def detect_language(text: str) -> str:
    kannada_chars = set('ಅಆಇಈಉಊಋಎಏಐಒಔಕಖಗಘಙಚಛಜಝಞಟಠಡಢಣತಥದಧನಪಫಬಭಮಯರಲವಶಷಸಹಳಱೞ')
    if any(char in kannada_chars for char in text):
        return "kn"
    return "en"

def _get_user_session(sender: str) -> Dict[str, Any]:
    if sender not in user_sessions:
        user_sessions[sender] = {
            "session_id": f"whatsapp_{sender}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "user_id": sender,
            "language": "kn",
            "created_at": datetime.now().isoformat(),
            "conversation_history": []
        }
    return user_sessions[sender]

# --- Meta Graph API helpers -------------------------------------------
def graph_get(path: str, params: dict = None) -> dict:
    url = f"{GRAPH_API_BASE}/{path.lstrip('/')}"
    if params is None:
        params = {}
    params["access_token"] = WHATSAPP_TOKEN
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def graph_post(path: str, json_payload: dict) -> dict:
    url = f"{GRAPH_API_BASE}/{path.strip('/')}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    r = requests.post(url, headers=headers, json=json_payload, timeout=30)
    r.raise_for_status()
    return r.json()

def download_media_from_meta(media_id: str, save_folder: Path, suggested_ext: Optional[str] = None) -> Optional[str]:
    try:
        # Step 1: get media URL
        meta = graph_get(media_id, params={})
        media_url = meta.get("url")
        mime_type = meta.get("mime_type") or ""
        if not media_url:
            logger.error("No media URL returned from Graph API for media_id=%s", media_id)
            return None

        # Step 2: download the bytes
        headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
        r = requests.get(media_url, headers=headers, stream=True, timeout=60)
        if r.status_code != 200:
            logger.error("Failed fetching media content: %s", r.status_code)
            return None

        ext = _safe_ext_from_mimetype(mime_type or suggested_ext)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{media_id}.{ext}"
        file_path = save_folder / filename
        with open(file_path, "wb") as f:
            for chunk in r.iter_content(4096):
                if chunk:
                    f.write(chunk)

        logger.info("Saved media -> %s", file_path)
        return str(file_path)
    except Exception as e:
        logger.error("Error downloading media: %s", e)
        return None

# --- Sending messages -------------------------------------------------
def send_text_message(to_number: str, text: str) -> bool:
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        logger.error("Cannot send message - token or phone_number_id missing.")
        return False
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text}
    }
    try:
        resp = graph_post(PHONE_NUMBER_ID, payload)
        logger.info("Sent text message: %s", resp)
        return True
    except Exception as e:
        logger.error("Error sending text message: %s", e)
        return False

def send_audio_via_link(to_number: str, audio_url: str, caption: Optional[str] = None) -> bool:
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        logger.error("Cannot send audio - token or phone_number_id missing.")
        return False
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "audio",
        "audio": {"link": audio_url}
    }
    try:
        resp = graph_post(PHONE_NUMBER_ID, payload)
        logger.info("Sent audio message: %s", resp)
        if caption:
            send_text_message(to_number, caption)
        return True
    except Exception as e:
        logger.error("Error sending audio message: %s", e)
        return False

# --- Workflow integration --------------------------------------------
async def run_workflow_async(workflow, user_input: str, session_id: str, user_id: str, language: str, image_url: Optional[str], audio_url: Optional[str]) -> Dict[str, Any]:
    try:
        resp = await workflow.run_conversation(
            user_input=user_input,
            session_id=session_id,
            user_id=user_id,
            language=language,
            image_url=image_url,
            audio_url=audio_url
        )
        return resp or {}
    except Exception as e:
        logger.exception("Workflow error: %s", e)
        return {"assistant_response": "ಕ್ಷಮಿಸಿ, ಒಂದು ದೋಷ ಸಂಭವಿಸಿದೆ. / Sorry, an error occurred."}

def call_workflow_and_respond(sender: str, user_input: str, image_path: Optional[str], audio_path: Optional[str]):
    try:
        workflow = get_workflow()
    except Exception as e:
        logger.error("Could not initialize workflow: %s", e)
        send_text_message(sender, "Sorry — internal bot error.")
        return

    session = _get_user_session(sender)
    session_id = session["session_id"]
    language = detect_language(user_input)
    session["language"] = language

    image_url_for_workflow = image_path
    audio_url_for_workflow = audio_path

    try:
        workflow_response = asyncio.run(run_workflow_async(
            workflow,
            user_input=user_input,
            session_id=session_id,
            user_id=sender,
            language=language,
            image_url=image_url_for_workflow,
            audio_url=audio_url_for_workflow
        ))
    except Exception as e:
        logger.exception("Exception running workflow: %s", e)
        workflow_response = {"assistant_response": "ಕ್ಷಮಿಸಿ, ಒಂದು ದೋಷ ಸಂಭವಿಸಿದೆ. / Sorry, an error occurred."}

    session["conversation_history"].append({
        "user_input": user_input,
        "assistant_response": workflow_response.get("assistant_response", ""),
        "timestamp": datetime.now().isoformat()
    })

    # Send text
    text_reply = workflow_response.get("assistant_response") or "Sorry, I couldn't generate a response."
    send_text_message(sender, text_reply)

    # If audio was generated
    try:
        audio_generated = bool(workflow_response.get("audio_generated"))
        audio_file_path = workflow_response.get("audio_path") or workflow_response.get("audio_response_path")
        if audio_generated and audio_file_path:
            source = Path(audio_file_path)
            if not source.exists():
                logger.error("Audio file missing: %s", audio_file_path)
            else:
                dest_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{source.name}"
                dest_path = UPLOADS_DIR / dest_name
                with open(source, "rb") as fr, open(dest_path, "wb") as fw:
                    fw.write(fr.read())
                if PUBLIC_BASE_URL:
                    public_url = f"{PUBLIC_BASE_URL}/uploads/{dest_name}"
                    logger.info("Sending audio reply link -> %s", public_url)
                    send_audio_via_link(sender, public_url)
                else:
                    logger.warning("PUBLIC_BASE_URL not set; cannot send audio media link.")
    except Exception as e:
        logger.exception("Error while sending generated audio: %s", e)

# --- Webhook Handler -----------------------------------------------
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            logger.info("Webhook verified")
            return challenge, 200
        else:
            logger.warning("Webhook verification failed: mode=%s token=%s", mode, token)
            return "Verification token mismatch", 403

    # POST — incoming message
    data = request.get_json(force=True, silent=True)
    logger.debug("Webhook received: %s", json.dumps(data or {}, indent=2)[:1000])

    if not data:
        return "no content", 400

    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for msg in value.get("messages", []) or []:
                    from_number = msg.get("from")
                    msg_type = msg.get("type")
                    text_body = ""
                    image_path = None
                    audio_path = None

                    if msg_type == "text":
                        text_body = msg.get("text", {}).get("body", "")
                        logger.info("Incoming text from %s: %s", from_number, text_body[:160])

                    elif msg_type in ("image", "audio", "voice", "document"):
                        media_obj = msg.get(msg_type, {})
                        media_id = media_obj.get("id")
                        mime_type = media_obj.get("mime_type") or media_obj.get("mimeType")
                        logger.info("Incoming media type=%s id=%s from=%s", msg_type, media_id, from_number)
                        if media_id:
                            folder = IMAGES_DIR if msg_type == "image" else AUDIO_IN_DIR
                            downloaded = download_media_from_meta(media_id, folder, suggested_ext=mime_type)
                            if downloaded:
                                if msg_type == "image":
                                    image_path = downloaded
                                else:
                                    audio_path = downloaded
                            else:
                                logger.error("Failed to download media id=%s", media_id)
                        text_body = msg.get("caption") or text_body

                    else:
                        # unsupported type
                        text_body = msg.get("text", {}).get("body", "")
                        logger.info("Unsupported incoming message type: %s", msg_type)

                    # Launch async processing thread
                    threading.Thread(
                        target=call_workflow_and_respond,
                        args=(from_number, text_body or "", image_path, audio_path),
                        daemon=True
                    ).start()

        return "EVENT_RECEIVED", 200
    except Exception as e:
        logger.exception("Error processing webhook payload: %s", e)
        return "error", 500

# Serve uploaded files
@app.route("/uploads/<path:filename>", methods=["GET"])
def serve_uploads(filename: str):
    try:
        return send_from_directory(UPLOADS_DIR, filename, as_attachment=False)
    except Exception as e:
        logger.error("Error serving upload '%s': %s", filename, e)
        return jsonify({"ok": False, "error": "file_not_found"}), 404

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "ok": True,
        "time": datetime.now().isoformat(),
        "active_sessions": len(user_sessions),
        "public_base_url_set": bool(PUBLIC_BASE_URL),
        "phone_number_id_set": bool(PHONE_NUMBER_ID)
    })

if __name__ == "__main__":
    logger.info("Starting Meta WhatsApp Flask app (A1 mode) …")
    app.run(host="0.0.0.0", port= 5000, debug= False)
