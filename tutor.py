from flask import Blueprint, render_template, request, jsonify, session 
from ai.notes import generate_notes_with_groq

from PIL import Image
import pytesseract
from flask import current_app
from utils.db_helpers import get_user_plan, is_admin

# ----- IMPORTANT: Change this to your real DB import -----
from models_pg import StudentProgress, TutorMessage, db
from datetime import date


pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


tutor_bp = Blueprint("tutor", __name__)


@tutor_bp.route("/tutor")
def tutor_home():
    return render_template("tutor.html")


# ---- PAUSE ROUTE ----
@tutor_bp.route("/tutor/pause", methods=["POST"])
def pause_explanation():
    session["paused_explanation"] = True
    return "paused"


# ---- CLEAR CHAT ----
@tutor_bp.route("/tutor/clear")
def clear_chat():
    session["chat_history"] = []
    session["current_topic"] = ""
    session["paused_explanation"] = False
    session["last_explanation"] = ""
    return "cleared"

# -------- SAVE STUDENT PROGRESS FUNCTION --------
def save_progress(user_id, topic, question, language):

    progress = StudentProgress(
        user_id=user_id,
        topic=topic,
        last_question=question,
        language=language,
        difficulty="normal",
        notes="Studied this topic"
    )

    db.session.add(progress)
    db.session.commit()

@tutor_bp.route("/tutor/ask", methods=["POST"])
def ask_tutor():

    data = request.json or {}

    question = data.get("question", "").strip()
    language = data.get("language", "en")
    input_type = data.get("input_type", "question")

    if not question:
        return jsonify({"answer": "Please ask a valid question."})

    # ----- USER / PLAN CHECK -----
    user_id = session.get("user_id", 1)

    plan = get_user_plan(user_id)

    # ---------- DAILY FREE LIMIT (10) ----------
    if plan == "free" and not is_admin():
        current_app.logger.info(
            "Tutor free-limit check for user_id=%s plan=%s",
            user_id,
            plan
        )

        today_count = TutorMessage.query.filter(
            TutorMessage.user_id == user_id,
            TutorMessage.created >= date.today()
        ).count()

        if today_count >= 10:
            return jsonify({
                "answer": "Daily free limit reached (10). Upgrade to Pro for unlimited Tutor access."
            }), 403

    # ----- LANGUAGE HANDLING -----
    if language == "hi":
        lang_prompt = "Reply ONLY in Hindi language."
    elif language == "kn":
        lang_prompt = "Reply ONLY in Kannada language."
    else:
        lang_prompt = "Reply ONLY in simple English."

    # ----- SESSION INIT -----
    session.setdefault("chat_history", [])
    session.setdefault("current_topic", "")
    session.setdefault("paused_explanation", False)
    session.setdefault("last_explanation", "")

    # ----- LOAD STUDENT MEMORY -----
    past = StudentProgress.query.filter_by(user_id=user_id).all()

    memory_text = ""
    for p in past[-5:]:
        memory_text += f"Previously studied: {p.topic}\n"

    # --------------------------------------------------
    # CONTINUE COMMAND
    # --------------------------------------------------
    if question.lower() == "continue":

        topic = session.get("current_topic", "")
        last = session.get("last_explanation", "")

        resume_prompt = f"""
{lang_prompt}

VERY IMPORTANT INSTRUCTIONS:

You are currently teaching ONLY this topic:

TOPIC: {topic}

This was your LAST explanation:
{last}

Now CONTINUE teaching EXACTLY the same topic.

STRICT RULES:
- Continue only from the next logical point
- Never change topic
- Never start a new subject
- Do NOT repeat what you already explained
- Continue in the same teaching style

End with one small checking question.
"""

        try:
            answer = generate_notes_with_groq(
                lesson=resume_prompt,
                mode="tutor",
                history=session["chat_history"]
            )
        except Exception:
            current_app.logger.exception("Tutor continue AI failed")
            return jsonify({"answer": "Tutor is temporarily unavailable."}), 500

        session["paused_explanation"] = False
        session["chat_history"].append({"role": "assistant", "content": answer})
        session["last_explanation"] = answer

        return jsonify({"answer": answer})

    # --------------------------------------------------
    # DOUBT MODE
    # --------------------------------------------------
    if session.get("paused_explanation"):

        doubt_prompt = f"""
{lang_prompt}

STUDENT MEMORY:
{memory_text}

You were explaining this topic:
{session.get('current_topic')}

Student doubt:
{question}

Explain ONLY this doubt clearly and simply.

Rules:
- Focus only on solving the doubt
- Do NOT continue the main lesson
- Do NOT repeat the full topic

At the END of your answer ALWAYS ask exactly this:

"Did that clear your doubt? Shall I continue from where we left off?"
"""

        try:
            answer = generate_notes_with_groq(
                lesson=doubt_prompt,
                mode="tutor",
                history=session["chat_history"]
            )
        except Exception:
            current_app.logger.exception("Tutor doubt AI failed")
            return jsonify({"answer": "Tutor is temporarily unavailable."}), 500

        session["chat_history"].append({"role": "assistant", "content": answer})

        return jsonify({"answer": answer})

    # --------------------------------------------------
    # FULL LESSON PASTE
    # --------------------------------------------------
    if input_type == "lesson":

        clean_topic = question[:120]

        session["current_topic"] = clean_topic
        session["paused_explanation"] = False
        session["last_explanation"] = ""

        lesson_prompt = f"""
{lang_prompt}

STUDENT MEMORY:
{memory_text}

The student pasted a full lesson.

Explain it like a friendly teacher:

- Step by step
- Simple language
- Clear points
- Easy examples
- Ask one small question at the end

LESSON:
{question}
"""

        try:
            answer = generate_notes_with_groq(
                lesson=lesson_prompt,
                mode="tutor",
                history=session["chat_history"]
            )
        except Exception:
            current_app.logger.exception("Tutor lesson AI failed")
            return jsonify({"answer": "Tutor is temporarily unavailable."}), 500

        session["chat_history"].append({"role": "assistant", "content": answer})
        session["last_explanation"] = answer

        save_progress(user_id, clean_topic, question, language)

        return jsonify({"answer": answer})

    # --------------------------------------------------
    # NORMAL QUESTION (NEW TOPIC)
    # --------------------------------------------------
    clean_topic = question.strip()

    session["current_topic"] = clean_topic[:120]
    session["paused_explanation"] = False
    session["last_explanation"] = ""

    normal_prompt = f"""
{lang_prompt}

STUDENT MEMORY:
{memory_text}

QUESTION:
{clean_topic}

Explain like a kind teacher with examples and simple steps.

At the end ask:

"Did you understand? Shall I explain differently?"
"""

    try:
        answer = generate_notes_with_groq(
            lesson=normal_prompt,
            mode="tutor",
            history=session["chat_history"]
        )
    except Exception:
        current_app.logger.exception("Tutor normal AI failed")
        return jsonify({"answer": "Tutor is temporarily unavailable."}), 500

    session["chat_history"].append({"role": "assistant", "content": answer})
    session["last_explanation"] = answer

    save_progress(user_id, clean_topic[:120], question, language)

    return jsonify({"answer": answer})


# -------- IMAGE OCR ANALYSIS --------
@tutor_bp.route("/tutor/analyze_image", methods=["POST"])
def analyze_image():

    if "image" not in request.files:
        return jsonify({"answer": "No image uploaded."})

    image_file = request.files["image"]

    try:
        img = Image.open(image_file)

        extracted_text = pytesseract.image_to_string(img, lang="eng")

        if not extracted_text.strip():
            return jsonify({"answer": "Could not detect readable text in the image."})

        prompt = f"""
The student uploaded an image containing this text:

{extracted_text}

Explain it like a friendly teacher:
- In simple steps
- With examples
- In easy language
- Ask one small question at the end
"""

        answer = generate_notes_with_groq(
            lesson=prompt,
            mode="tutor"
        )

        return jsonify({"answer": answer})

    except Exception as e:
        return jsonify({"answer": "Error analyzing image. Please try a clearer image."})

@tutor_bp.route("/tutor/dashboard")
def student_dashboard():

    user_id = session.get("user_id", 1)

    progress = StudentProgress.query.filter_by(user_id=user_id).all()

    return render_template("student_dashboard.html", progress=progress)

@tutor_bp.route("/tutor/progress_api")
def progress_api():
    user_id = session.get("user_id")

    data = StudentProgress.query.filter_by(user_id=user_id).all()

    result = []
    for p in data:
        result.append({
            "topic": p.topic,
            "language": p.language
        })

    return jsonify(result)

@tutor_bp.route("/tutor/reset_topic", methods=["POST"])
def reset_topic():
    session["current_topic"] = ""
    session["paused_explanation"] = False
    session["last_explanation"] = ""
    return "reset"

@tutor_bp.route("/tutor/get_username")
def get_username():
    return jsonify({
        "username": session.get("username", "Student")
    })

@tutor_bp.route("/tutor/set_nickname", methods=["POST"])
def set_nickname():
    data = request.json or {}
    name = data.get("name", "").strip()

    if name:
        session["custom_name"] = name
        return jsonify({"status": "saved"})

    return jsonify({"status": "error"})
