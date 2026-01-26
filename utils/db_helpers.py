from models_pg import User, Note
from datetime import date
from flask import session


def get_user_plan(user_id):
    """
    Get plan of user.
    Admin is always treated as PRO.
    """
    user = User.query.get(user_id)

    if not user:
        return "free"

    # Admin automatically gets PRO privileges
    if user.username == "admin":
        return "pro"

    return user.plan


def is_admin():
    """
    More reliable admin check using DB instead of only session
    """
    user_id = session.get("user_id")

    if not user_id:
        return False

    user = User.query.get(user_id)

    if user and user.username == "admin":
        return True

    return False


def get_usage(user_id):
    """
    Get daily and total note usage.
    Admin gets unlimited usage.
    """

    # Admin bypass
    if is_admin():
        return {
            "today": 0,
            "total": 0,
            "admin": True
        }

    today_count = Note.query.filter_by(
        user_id=user_id,
        created=date.today()
    ).count()

    total_count = Note.query.filter_by(
        user_id=user_id
    ).count()

    return {
        "today": today_count,
        "total": total_count,
        "admin": False
    }
