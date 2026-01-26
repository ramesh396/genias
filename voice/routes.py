from flask import Blueprint, request, Response
import os
from dotenv import load_dotenv

from google.cloud import texttospeech

load_dotenv()

# ---- CREATE BLUEPRINT ----
voice_bp = Blueprint("voice", __name__)

# ---- LOAD GOOGLE CREDENTIALS SAFELY ----
cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

if cred_path:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
else:
    print("⚠️ WARNING: GOOGLE_APPLICATION_CREDENTIALS not set. Voice feature disabled.")


# ---- ROUTE ----
@voice_bp.route("/voice")
def voice():

    text = request.args.get("text", "").strip()
    voice_name = request.args.get("voice", "en-IN-Neural2-C")

    if not text:
        return "No text provided", 400

    # Limit size for Google API
    MAX_LENGTH = 4500
    if len(text) > MAX_LENGTH:
        text = text[:MAX_LENGTH]

    # If credentials missing → fail nicely
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        return "Voice service not configured", 503

    try:
        client = texttospeech.TextToSpeechClient()

        synthesis_input = texttospeech.SynthesisInput(
            text=text
        )

        # Detect language
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
                "Cache-Control": "no-cache"
            }
        )

    except Exception as e:
        print("TTS Error:", str(e))
        return "Error generating voice", 500
