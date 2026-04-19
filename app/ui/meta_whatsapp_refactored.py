#!/usr/bin/env python3
"""
Final Merged Version
---------------------
- Uses clean "sending method" from Code 1 (graph_post_messages)
- Integrates full KisanVoice workflow from Code 2
- Supports: text, image, audio
- Sends AI response + A1 audio link
- Single-file production-ready Flask application
"""

import os
import json
import threading
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
import requests
from loguru import logger

# -----------------------------
# Load Environment Variables
# -----------------------------
load_dotenv()

WHATSAPP_TOKEN   = os.getenv("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID  = os.getenv("PHONE_NUMBER_ID", "")
VERIFY_TOKEN     = os.getenv("VERIFY_TOKEN", "")
PUBLIC_BASE_URL  = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
GRAPH_VERSION    = "v17.0"
GRAPH_BASE_URL   = f"https://graph.facebook.com/{GRAPH_VERSION}"

if not WHATSAPP_TOKEN:
    logger.warning("WHATSAPP_TOKEN is missing!")
if not PHONE_NUMBER_ID:
    logger.warning("PHONE_NUMBER_ID is missing!")
if not VERIFY_TOKEN:
    logger.warning("VERIFY_TOKEN is missing! Webhook verification will fail.")
if not PUBLIC_BASE_URL:
    logger.warning("PUBLIC_BASE_URL is missing! Audio cannot be sent.")

# -----------------------------
# Imports from your project
# -----------------------------
import sys
THIS_DIR = Path(__file__).resolve().parent
sys.path.append(str(THIS_DIR))
sys.path.append(str(THIS_DIR.parent))

try:
    from core.workflow import get_workflow
except Exception as e:
    logger.error(f"Could not import KisanVoice workflow: {e}")
    raise

# -----------------------------
# Folder Setup
# -----------------------------
BASE_DIR = THIS_DIR
DOWNLOADS_DIR = BASE_DIR / "downloads"
IMAGES_DIR = DOWNLOADS_DIR / "images"
AUDIO_IN_DIR = DOWNLOADS_DIR / "audio"
UPLOADS_DIR = BASE_DIR / "uploads"

for d in [IMAGES_DIR, AUDIO_IN_DIR, UPLOADS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# -----------------------------
# Flask App + Memory
# -----------------------------
app = Flask(__name__)
user_sessions: Dict[str, Dict[str, Any]] = {}

# -----------------------------
# Utils
# -----------------------------
def _safe_ext(mime: str) -> str:
    if not mime:
        return "bin"
    ext = mime.split("/")[-1].lower()
    return "jpg" if ext == "jpeg" else ext

def detect_language(text: str) -> str:
    # Full Kannada characters
    kannada = set(
        'ಀಁಂಃ಄ಅಆಇಈಉಊಋೠಌೡಎಏಐಒಓಔ'
        'ಕಖಗಘಙಚಛಜಝಞಟಠಡಢಣತಥದಧನ'
        'ಪಫಬಭಮಯರಱಲಳವಶಷಸಹ'
        '಼ಽಾಿೀುೂೃೄೆೇೈೊೋೌ್'
        'ೕೖೞ೟ೠೡ'
        '೦೧೨೩೪೫೬೭೮೯'
        '।॥'
    )

    # Full Hindi / Devanagari characters
    hindi = set(
        'ऀँंःऄअआइईउऊऋॠऌॡएऐओऔ'
        'कखगघङचछजझञटठडढणतथदधन'
        'पफबभमयरऱलळऴवशषसह'
        '़ऽािीुूृॄॅॆेैॉॊोौ्॒॑ॕॖॗ'
        '०१२३४५६७८९'
        '।॥'
    )

    # 1️⃣ Kannada detection
    if any(c in kannada for c in text):
        return "kn"

    # 2️⃣ Hindi detection
    if any(c in hindi for c in text):
        return "hi"

    # 3️⃣ English is the fallback
    return "en"


def get_session(sender: str):
    if sender not in user_sessions:
        user_sessions[sender] = {
            "session_id": f"wa_{sender}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "language": "kn",
            "history": []
        }
    return user_sessions[sender]

# -----------------------------
# Clean Meta Sender (From Code 1)
# -----------------------------
def graph_post_messages(payload: dict) -> dict:
    url = f"{GRAPH_BASE_URL}/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}

    logger.info(f"POST → Meta: {payload}")

    r = requests.post(url, headers=headers, json=payload, timeout=30)

    logger.info(f"Meta Response Status: {r.status_code}")
    logger.info(f"Meta Response Body: {r.text}")

    r.raise_for_status()
    return r.json()



def send_whatsapp_text(to: str, text: str) -> bool:
    """Clean Meta text sending method."""
    try:
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text}
        }
        graph_post_messages(payload)
        return True
    except Exception as e:
        logger.error(f"Error sending text: {e}")
        return False


def send_whatsapp_audio_link(to: str, url: str) -> bool:
    """A1 audio sending (PUBLIC_BASE_URL)."""
    try:
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "audio",
            "audio": {
                "link": url,
            }
        }
        logger.info(f"Sending audio payload: {payload}")
        graph_post_messages(payload)
        return True
    except Exception as e:
        logger.error(f"Error sending audio link: {e}")
        return False



# -----------------------------
# Media Download (From Code 2)
# -----------------------------
def download_media(media_id: str, save_dir: Path, mime: Optional[str]) -> Optional[str]:
    try:
        # STEP 1: GET metadata
        meta_url = f"{GRAPH_BASE_URL}/{media_id}"
        meta = requests.get(meta_url, params={"access_token": WHATSAPP_TOKEN}).json()
        file_url = meta.get("url")
        mime_type = meta.get("mime_type") or mime

        if not file_url:
            logger.error("No file URL received from Meta")
            return None

        # STEP 2: Download file bytes
        headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
        r = requests.get(file_url, headers=headers, stream=True, timeout=60)

        ext = _safe_ext(mime_type)
        name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{media_id}.{ext}"
        file_path = save_dir / name

        with open(file_path, "wb") as f:
            for chunk in r.iter_content(4096):
                if chunk:
                    f.write(chunk)

        logger.info(f"Downloaded media → {file_path}")
        return str(file_path)

    except Exception as e:
        logger.error(f"Media download failed: {e}")
        return None


# -----------------------------
# Workflow Integration (From Code 2)
# -----------------------------
async def run_workflow(workflow, session, sender, text, image_path, audio_path):
    try:
        resp = await workflow.run_conversation(
            user_input=text,
            session_id=session["session_id"],
            user_id=sender,
            language=session["language"],
            image_url=image_path,
            audio_url=audio_path
        )
        return resp or {}
    except Exception as e:
        logger.error(f"Workflow error: {e}")
        return {"assistant_response": "ಕ್ಷಮಿಸಿ, ದೋಷ ಸಂಭವಿಸಿದೆ. / Sorry, an error occurred."}


def process_message_background(sender, text, image_path, audio_path):
    workflow = get_workflow()
    session = get_session(sender)
    session["language"] = detect_language(text)

    resp = asyncio.run(
        run_workflow(workflow, session, sender, text, image_path, audio_path)
    )

    # Send text reply
    reply = resp.get("assistant_response", "")
    send_whatsapp_text(sender, reply)

    # -----------------------
    # AUDIO HANDLING (PATCHED)
    # -----------------------
    if resp.get("audio_generated"):
        audio_file = Path(resp.get("audio_path"))
        if audio_file.exists():
            new_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{audio_file.name}"
            dest = UPLOADS_DIR / new_name
            dest.write_bytes(audio_file.read_bytes())

            public_url = f"{PUBLIC_BASE_URL}/uploads/{new_name}"

            # 1️⃣ Send audio as WhatsApp audio file
            send_whatsapp_audio_link(sender, public_url)

            # 2️⃣ ALSO send audio URL as a text message
            #send_whatsapp_text(sender, f"🎧 Your audio response is ready:\n{public_url}")
            
    #logger.error(f"WORKFLOW RAW RESPONSE = {resp}")



# -----------------------------
# Payload Extractor (From Code 1)
# -----------------------------
def extract_payload(payload: Dict[str, Any]) -> Tuple[str, str, dict]:
    """
    Return (sender, text, extra)
    """
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            msg_list = change.get("value", {}).get("messages", [])
            if not msg_list:
                continue

            msg = msg_list[0]
            sender = msg.get("from")
            msg_type = msg.get("type")
            text = ""
            image_path = None
            audio_path = None

            if msg_type == "text":
                text = msg["text"]["body"]

            elif msg_type in ("image", "audio", "voice"):
                media = msg[msg_type]
                media_id = media.get("id")
                mime = media.get("mime_type")
                folder = IMAGES_DIR if msg_type == "image" else AUDIO_IN_DIR
                downloaded = download_media(media_id, folder, mime)

                if msg_type == "image":
                    image_path = downloaded
                else:
                    audio_path = downloaded

                text = msg.get("caption") or ""

            return sender, text, {
                "image": image_path,
                "audio": audio_path
            }

    return None, None, {}


# -----------------------------
# Webhook Routes
# -----------------------------
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Invalid verify token", 403


@app.route("/webhook", methods=["POST"])
def receive_msg():
    data = request.get_json()
    sender, text, extra = extract_payload(data)

    if not sender or text is None:
        return "ignored", 200

    threading.Thread(
        target=process_message_background,
        args=(sender, text, extra.get("image"), extra.get("audio")),
        daemon=True
    ).start()

    return "EVENT_RECEIVED", 200


# -----------------------------
# Serve Audio Files
# -----------------------------
@app.route("/uploads/<path:f>", methods=["GET"])
def serve_uploads(f):
    file_path = UPLOADS_DIR / f

    if not file_path.exists():
        return "Not found", 404

    # --- Set correct MIME for audio ---
    if f.lower().endswith(".mp3"):
        return send_from_directory(
            UPLOADS_DIR,
            f,
            mimetype="audio/mpeg"
        )
    
    return send_from_directory(UPLOADS_DIR, f)


# -----------------------------
# Health
# -----------------------------
@app.route("/health")
def health():
    return {"ok": True, "sessions": len(user_sessions)}


# -----------------------------
# Run App
# -----------------------------
if __name__ == "__main__":
    logger.info("Starting FINAL Meta WhatsApp Flask bot…")
    app.run(host="0.0.0.0", port=5000 , debug=False)
