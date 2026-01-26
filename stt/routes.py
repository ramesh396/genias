from flask import Blueprint, request, jsonify
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

stt_bp = Blueprint("stt", __name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

@stt_bp.route("/speech_to_text", methods=["POST"])
def speech_to_text():

    audio = request.files.get("audio")

    if not audio:
        return jsonify({"error": "No audio received"}), 400

    try:
        client = Groq(api_key=GROQ_API_KEY)

        # Save temporarily
        temp_path = "temp_audio.wav"
        audio.save(temp_path)

        with open(temp_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(temp_path, file.read()),
                model="whisper-large-v3-turbo"
            )

        os.remove(temp_path)

        return jsonify({"text": transcription.text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
