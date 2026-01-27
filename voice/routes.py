from flask import Blueprint, request, Response
import os
import json
import tempfile
from dotenv import load_dotenv

from google.cloud import texttospeech

load_dotenv()

# ---- CREATE BLUEPRINT ----
voice_bp = Blueprint("voice", __name__)

# ---------------------------------------------------
# LOAD GOOGLE TTS CREDENTIALS FROM ENV (RENDER SAFE)
# ---------------------------------------------------

tts_json = os.getenv("GOOGLE_TTS_JSON")

TEMP_CRED_PATH = None

if tts_json:
    try:
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".json"
        )
        temp_file.write(tts_json.encode("utf-8"))
        temp_file.close()

        TEMP_CRED_PATH = temp_file.name
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = TEMP_CRED_PATH

        print("✅ Google TTS credentials loaded from env")

    except Exception as e:
        print("❌ Failed to write Google TTS credentials:", str(e))

else:
    print("⚠️ GOOGLE_TTS_JSON not set — voice disabled")

# ---------------------------------------------------
# ROUTE
# ---------------------------------------------------

@voice_bp.route("/voice")
def voice():

    text = request.args.get("text", "").strip()
    voice_name = request.args.get("voice", "en-IN-Neural2-C")

    if not text:
        return "No text provided", 400

    # Limit length for Google API
    MAX_LENGTH = 4500
    if len(text) > MAX_LENGTH:
        text = text[:MAX_LENGTH]

    # If credentials missing → fail cleanly
    if not TEMP_CRED_PATH:
        return "Voice service not configured", 503

    try:
        client = texttospeech.TextToSpeechClient()

        synthesis_input = texttospeech.SynthesisInput(
            text=text
        )

        # Language detection
        if voice_name.startswith("hi-IN"):
            language_code = "hi-IN"
        elif voice_name.startswith("kn-IN"):
            language_code = "kn-IN"
        else:
            language_code = "en-IN"

        voice_params = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_name
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=0.96,
            pitch=0.0,
            volume_gain_db=0.0
        )

        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice_params,
            audio_config=audio_config
        )

        return Response(
            response.audio_content,
            mimetype="audio/mpeg",
            headers={
                "Cache-Control": "no-cache",
                "Content-Type": "audio/mpeg"
            }
        )

    except Exception as e:
        print("❌ TTS Error:", str(e))
        return f"Error generating voice: {str(e)}", 500
