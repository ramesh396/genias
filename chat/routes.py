from flask import Blueprint, request, session, redirect, render_template
from datetime import date

from models_pg import db, ChatSession, Chat, User
from utils.db_helpers import get_user_plan, is_admin
from ai.groq import groq_generate

from chat.utils import get_chat_context, update_session_title
from flask import current_app

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/chat")
def chat_page():
    if "user_id" not in session:
        return redirect("/")

    sessions = ChatSession.query.filter_by(
        user_id=session["user_id"]
    ).order_by(ChatSession.id.desc()).all()

    return render_template("chat.html", sessions=sessions)

from flask import request, session, current_app
from datetime import date

@chat_bp.route("/chat_stream", methods=["POST"])
def chat_stream():

    if "user_id" not in session:
        return "Unauthorized", 401

    # -------- GET INPUTS --------
    question = request.form.get("question", "").strip()
    image = request.form.get("image")

    if not question and not image:
        return "Question or image required", 400

    user_id = session["user_id"]
    plan = get_user_plan(user_id)

    # ---------- FREE PLAN LIMIT ----------
    if plan == "free" and not is_admin():
        today_count = Chat.query.filter(
            Chat.user_id == user_id,
            Chat.created == date.today()
        ).count()

        if today_count >= 10:
            return "Daily chat limit reached. Upgrade to Pro.", 403

    # ---------- CHAT SESSION LOGIC ----------
    session_id = request.form.get("session_id")

    if session_id:
        session_id = int(session_id)
    else:
        new_session = ChatSession(
            user_id=user_id,
            title="New Chat"
        )
        db.session.add(new_session)
        db.session.commit()
        session_id = new_session.id

    # Get previous context
    memory = get_chat_context(user_id, session_id, limit=4)

    # ---------- AI GENERATION ----------
    try:
        if image:
            prompt = f"""
You are an AI Tutor.

The student has uploaded an image.

INSTRUCTIONS:
- Carefully analyze the image
- Understand diagrams, text or questions
- Explain clearly and step-by-step
- Exam oriented explanation
- Simple student friendly language

PREVIOUS CONTEXT (if relevant):
{memory}

ANSWER:
"""
            answer = groq_generate(
                prompt=prompt,
                image=image,
                max_tokens=400
            )
        else:
            prompt = f"""
You are a student doubt-solving assistant.

RULES:
- Answer only the current question
- Be clear and concise
- Exam-oriented explanations
- Use previous context ONLY if relevant

PREVIOUS CONTEXT:
{memory}

QUESTION:
{question}

ANSWER:
"""
            answer = groq_generate(
                prompt=prompt,
                max_tokens=300,
                temperature=0.15
            )

    except Exception:
        # 🔐 LOG FULL ERROR SAFELY
        current_app.logger.exception("Groq API failed in chat_stream")
        return "AI is temporarily unavailable. Please try again later.", 500

    # -------- SAVE CHAT MESSAGE --------
    try:
        new_chat = Chat(
            user_id=user_id,
            session_id=session_id,
            question=question if question else "[Image Uploaded]",
            answer=answer
        )
        db.session.add(new_chat)
        db.session.commit()

        update_session_title(
            session_id,
            question if question else "Image Chat"
        )

    except Exception:
        current_app.logger.exception("Database error while saving chat")
        return "Failed to save chat. Please try again.", 500

    return answer


@chat_bp.route("/chat/delete/<int:session_id>", methods=["POST"])
def delete_chat_session(session_id):
    if "user_id" not in session:
        return "Unauthorized", 401

    Chat.query.filter_by(
        user_id=session["user_id"],
        session_id=session_id
    ).delete()

    ChatSession.query.filter_by(
        user_id=session["user_id"],
        id=session_id
    ).delete()

    db.session.commit()

    return "OK"


@chat_bp.route("/chat/new")
def new_chat():
    if "user_id" not in session:
        return redirect("/")

    return redirect("/chat")


@chat_bp.route("/chat/session/<int:session_id>")
def get_chat_session(session_id):

    if "user_id" not in session:
        return {"error": "Unauthorized"}, 401

    messages = Chat.query.filter_by(
        user_id=session["user_id"],
        session_id=session_id
    ).order_by(Chat.id.asc()).all()

    data = {
        "messages": [
            {
                "question": m.question,
                "answer": m.answer
            }
            for m in messages
        ]
    }

    return data


@chat_bp.route("/chat/sessions")
def list_sessions():

    if "user_id" not in session:
        return {"error": "Unauthorized"}, 401

    sessions = ChatSession.query.filter_by(
        user_id=session["user_id"]
    ).order_by(ChatSession.id.desc()).all()

    return {
        "sessions": [
            {"id": s.id, "title": s.title or "New Chat"}
            for s in sessions
        ]
    }

