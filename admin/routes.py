from flask import Blueprint, render_template, session, abort, redirect, url_for
from models_pg import db, User, Note
from admin.utils import get_admin_stats
from sqlalchemy import func

admin_bp = Blueprint("admin", __name__)


def is_admin():
    return session.get("username") == "admin"


@admin_bp.route("/admin")
def admin_dashboard():
    if "user_id" not in session:
        return redirect("/")

    if not is_admin():
        abort(403)

    users = db.session.query(
        User.id,
        User.username,
        User.email,
        User.plan,
        func.count(Note.id).label("total_notes")
    ).outerjoin(Note, User.id == Note.user_id) \
     .group_by(User.id) \
     .order_by(func.count(Note.id).desc()) \
     .all()

    stats = get_admin_stats()

    return render_template(
        "admin.html",
        users=users,
        stats=stats
    )


@admin_bp.route("/admin/delete_user/<int:user_id>")
def delete_user(user_id):
    if not is_admin():
        abort(403)

    user = User.query.get(user_id)

    if not user:
        return "User not found"

    if user.username == "admin":
        return "Admin cannot be deleted"

    # Delete user's notes first (to avoid foreign key issues)
    Note.query.filter_by(user_id=user_id).delete()

    db.session.delete(user)
    db.session.commit()

    return redirect(url_for("admin.admin_dashboard"))
