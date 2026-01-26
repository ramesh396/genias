from flask import Blueprint, render_template, session, redirect, request, current_app
from models_pg import db, Note, MemoryTest
from ai.groq import groq_generate
from memory.utils import evaluate_memory_answers
from utils.security import verify_csrf
from utils.db_helpers import get_user_plan, is_admin

memory_bp = Blueprint("memory", __name__)


# ---------------- MEMORY PAGE ----------------
@memory_bp.route("/memory")
def memory_page():
    if "user_id" not in session:
        return redirect("/")

    user_id = session["user_id"]

    try:
        notes = Note.query.filter_by(
            user_id=user_id
        ).order_by(Note.id.desc()).all()
    except Exception:
        current_app.logger.exception("Failed to load notes for memory page")
        return "Unable to load memory page", 500

    return render_template("memory.html", notes=notes)


# ---------------- START MEMORY TEST ----------------
@memory_bp.route("/memory/start")
def memory_start():

    if "user_id" not in session:
        return redirect("/")

    user_id = session["user_id"]
    plan = get_user_plan(user_id)

    if plan == "free" and not is_admin():
        return redirect("/pricing")

    note_id = request.args.get("note_id")

    note = Note.query.filter_by(
        id=note_id,
        user_id=user_id
    ).first()

    if not note:
        return "Note not found", 404

    prompt = f"""
Create EXACTLY 5 ACTIVE RECALL questions.

NOTES:
{note.content}

QUESTIONS:
"""

    try:
        output = groq_generate(prompt, max_tokens=300, temperature=0.2)
    except Exception:
        current_app.logger.exception("Groq API failed in memory_start")
        return "AI is temporarily unavailable. Please try again later.", 500

    questions = [q.strip() for q in output.split("\n") if q.strip()]
    questions = questions[:5]

    session["memory_questions"] = questions
    session["memory_note_id"] = note_id

    return render_template("memory_test.html", questions=questions)


# ---------------- SUBMIT MEMORY TEST ----------------
@memory_bp.route("/memory/submit", methods=["POST"])
def memory_submit():

    if "user_id" not in session:
        return redirect("/")

    verify_csrf()

    user_id = session["user_id"]
    plan = get_user_plan(user_id)

    if plan == "free" and not is_admin():
        return redirect("/pricing")

    questions = session.get("memory_questions", [])
    note_id = session.get("memory_note_id")

    if not questions or not note_id:
        current_app.logger.warning("Memory submit without active session")
        return redirect("/memory")

    answers = [
        request.form.get(f"answer{i+1}", "")
        for i in range(len(questions))
    ]

    try:
        score, total, percentage = evaluate_memory_answers(
            questions, answers
        )
    except Exception:
        current_app.logger.exception("Memory answer evaluation failed")
        return "Evaluation failed. Please try again.", 500

    try:
        test = MemoryTest(
            user_id=user_id,
            note_id=note_id,
            score=score,
            total=total,
            percentage=percentage
        )

        db.session.add(test)
        db.session.commit()

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Database error saving memory test")
        return "Failed to save memory test result", 500

    return redirect(f"/memory/result/{test.id}")


# ---------------- MEMORY RESULT ----------------
@memory_bp.route("/memory/result/<int:test_id>")
def memory_result(test_id):

    if "user_id" not in session:
        return redirect("/")

    try:
        result = MemoryTest.query.filter_by(
            id=test_id,
            user_id=session["user_id"]
        ).first()
    except Exception:
        current_app.logger.exception("Failed to fetch memory test result")
        return "Unable to load result", 500

    if not result:
        return "Result not found", 404

    return render_template(
        "memory_result.html",
        percentage=result.percentage
    )
