from flask import Blueprint, render_template, request, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash

from models_pg import db, User, Note, Chat, ChatSession, MemoryTest
from utils.security import verify_csrf

user_bp = Blueprint("user_bp", __name__)


@user_bp.route("/settings", methods=["GET", "POST"])
def settings():
    if "user_id" not in session:
        return redirect("/")

    message = ""

    if request.method == "POST":
        verify_csrf()

        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")

        if not old_password or not new_password:
            message = "All fields are required"
        else:
            user = User.query.get(session["user_id"])

            if user and check_password_hash(user.password, old_password):
                user.password = generate_password_hash(new_password)
                db.session.commit()
                message = "✅ Password updated"
            else:
                message = "❌ Old password incorrect"

    return render_template(
        "settings.html",
        username=session.get("username"),
        message=message
    )


@user_bp.route("/delete_account", methods=["POST"])
def delete_account():
    verify_csrf()

    if "user_id" not in session:
        return redirect("/")

    user_id = session["user_id"]

    # Delete all related data using ORM
    Note.query.filter_by(user_id=user_id).delete()
    Chat.query.filter_by(user_id=user_id).delete()
    ChatSession.query.filter_by(user_id=user_id).delete()
    MemoryTest.query.filter_by(user_id=user_id).delete()

    # Finally delete user
    User.query.filter_by(id=user_id).delete()

    db.session.commit()

    session.clear()
    return redirect("/")
