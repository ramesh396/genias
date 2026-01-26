from flask import Blueprint, session, render_template, redirect
from datetime import date, timedelta

from models_pg import db, Chat, Note

progress_bp = Blueprint("progress", __name__)


@progress_bp.route("/progress")
def progress_dashboard():

    if "user_id" not in session:
        return redirect("/")

    user_id = session["user_id"]

    # -------- BASIC TOTALS --------
    total_notes = Note.query.filter_by(user_id=user_id).count()
    total_chats = Chat.query.filter_by(user_id=user_id).count()

    today = date.today()

    chats_today = Chat.query.filter(
        Chat.user_id == user_id,
        Chat.created == today
    ).count()

    notes_today = Note.query.filter(
        Note.user_id == user_id,
        Note.created == today
    ).count()

    # -------- LAST 7 DAYS ACTIVITY --------
    last_week = []

    for i in range(7):
        day = today - timedelta(days=i)

        chat_count = Chat.query.filter(
            Chat.user_id == user_id,
            Chat.created == day
        ).count()

        note_count = Note.query.filter(
            Note.user_id == user_id,
            Note.created == day
        ).count()

        last_week.append({
            "date": day.strftime("%d %b"),
            "chats": chat_count,
            "notes": note_count
        })

    last_week.reverse()

    # -------- TOPIC WISE NOTES ANALYTICS --------

    topic_stats = db.session.query(
        Note.lesson,
        db.func.count(Note.id)
    ).filter_by(user_id=user_id).group_by(Note.lesson).all()

    topic_data = []

    for lesson, count in topic_stats:
        topic_data.append({
            "topic": lesson or "General",
            "notes": count
        })

    # -------- MOST ASKED CHAT TOPICS --------

    chat_topic_stats = db.session.query(
        Chat.question,
        db.func.count(Chat.id)
    ).filter_by(user_id=user_id).group_by(Chat.question).limit(10).all()

    chat_topic_data = []

    for q, count in chat_topic_stats:
        chat_topic_data.append({
            "topic": q[:40] + "..." if len(q) > 40 else q,
            "count": count
        })

    return render_template(
        "progress.html",
        total_notes=total_notes,
        total_chats=total_chats,
        chats_today=chats_today,
        notes_today=notes_today,
        last_week=last_week,
        topic_data=topic_data,
        chat_topic_data=chat_topic_data
    )
