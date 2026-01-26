from flask import Blueprint, render_template, session, redirect, request, Response
from datetime import date
import io

from models_pg import db, Note
from utils.db_helpers import get_user_plan, is_admin, get_usage
from ai.notes import generate_notes_with_groq
from notes.utils import clean_html
from utils.security import verify_csrf

from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

from PIL import Image
import pytesseract
from flask import current_app
notes_bp = Blueprint("notes", __name__)


@notes_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    user_id = session["user_id"]
    search = request.args.get("search", "")

    if search:
        notes = Note.query.filter(
            Note.user_id == user_id,
            Note.lesson.ilike(f"%{search}%")
        ).order_by(Note.id.desc()).all()
    else:
        notes = Note.query.filter_by(
            user_id=user_id
        ).order_by(Note.id.desc()).all()

    plan = get_user_plan(user_id)
    usage = get_usage(user_id)

    return render_template(
        "index.html",
        notes=notes,
        search=search,
        plan=plan,
        usage=usage
    )


@notes_bp.route("/generate_stream", methods=["POST"])
def generate_stream():
    if "user_id" not in session:
        return "Unauthorized", 401
    verify_csrf()

    user_id = session["user_id"]
    plan = get_user_plan(user_id)

    lesson = request.form.get("lesson", "")
    mode = request.form.get("mode", "board")
    user_prompt = request.form.get("user_prompt", "")

    # FREE LIMIT CHECK
    if plan == "free" and not is_admin():
        today_count = Note.query.filter_by(
            user_id=user_id,
            created=date.today()
        ).count()

        if today_count >= 5:
            return "Daily free limit reached. Upgrade to Pro.", 403

    # MCQ MODE – PRO ONLY
    if mode == "mcq" and plan == "free" and not is_admin():
        return "MCQ mode is Pro only. Upgrade to unlock.", 403

    try:
        output = generate_notes_with_groq(
            lesson=lesson,
            mode=mode,
            user_prompt=user_prompt,
            plan=plan
        )
    except Exception:
      current_app.logger.exception("Groq API failed in generate_stream")
      return "AI service temporarily unavailable. Please try again.", 500


    try:
        new_note = Note(
            user_id=user_id,
            lesson=lesson,
            content=output,
            created=date.today()
        )

        db.session.add(new_note)
        db.session.commit()
    except Exception as e:
        print("DB Error:", str(e))
        return "Failed to save note in database", 500

    return Response(output, mimetype="text/plain")


@notes_bp.route("/note/<int:note_id>")
def note_view(note_id):
    if "user_id" not in session:
        return "Unauthorized", 401

    note = Note.query.filter_by(
        id=note_id,
        user_id=session["user_id"]
    ).first()

    if not note:
        return "Note not found", 404

    clean_content = clean_html(note.content)

    formatted_note = {
        "id": note.id,
        "lesson": note.lesson,
        "content": clean_content
    }

    return render_template("view_note.html", note=formatted_note)


@notes_bp.route("/delete/<int:note_id>", methods=["POST"])
def delete_note(note_id):
    if "user_id" not in session:
        return "Unauthorized", 401

    verify_csrf()

    note = Note.query.filter_by(
        id=note_id,
        user_id=session["user_id"]
    ).first()

    if note:
        db.session.delete(note)
        db.session.commit()

    return "OK"


@notes_bp.route("/download/<int:note_id>")
def download(note_id):
    if "user_id" not in session:
        return redirect("/")

    plan = get_user_plan(session["user_id"])

    if plan == "free" and not is_admin():
        return redirect("/upgrade")

    note = Note.query.filter_by(
        id=note_id,
        user_id=session["user_id"]
    ).first()

    if not note:
        return "Note not found", 404

    buf = io.BytesIO()
    pdf = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()

    story = [Paragraph(note.lesson, styles["Title"])]

    clean_pdf = clean_html(note.content)

    for line in clean_pdf.split("\n"):
        story.append(Paragraph(line, styles["Normal"]))

    pdf.build(story)

    buf.seek(0)

    return Response(
        buf,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f"attachment;filename={note.lesson}.pdf"
        }
    )


@notes_bp.route("/notes_list")
def notes_list():
    if "user_id" not in session:
        return "Unauthorized", 401

    user_id = session["user_id"]

    notes = Note.query.filter_by(
        user_id=user_id
    ).order_by(Note.id.desc()).all()

    return render_template(
        "partials/notes_list.html",
        notes=notes
    )

@notes_bp.route("/edit/<int:note_id>", methods=["GET", "POST"])
def edit_note(note_id):
    if "user_id" not in session:
        return redirect("/")

    note = Note.query.filter_by(
        id=note_id,
        user_id=session["user_id"]
    ).first()

    if not note:
        return "Note not found", 404

    if request.method == "POST":
        verify_csrf()

        lesson = request.form.get("lesson")
        content = request.form.get("content")

        note.lesson = lesson
        note.content = content

        db.session.commit()

        return redirect("/dashboard")

    return render_template("edit_note.html", note=note)


@notes_bp.route("/generate_from_image", methods=["POST"])
def generate_from_image():

    if "user_id" not in session:
        return "Unauthorized", 401

    verify_csrf()

    if "image" not in request.files:
        return "No image uploaded", 400

    file = request.files["image"]

    try:
        img = Image.open(file)

        extracted_text = pytesseract.image_to_string(img, lang="eng")

        if not extracted_text.strip():
            return "Could not detect readable text in the image.", 400

        # NOW USE YOUR EXISTING AI FUNCTION
        output = generate_notes_with_groq(
            lesson="Image Based Notes",
            mode=request.form.get("mode", "board"),
            user_prompt=extracted_text,
            plan=get_user_plan(session["user_id"])
        )

        return Response(output, mimetype="text/plain")

    except Exception as e:
        print("OCR Error:", str(e))
        return "Error processing image", 500
