from models_pg import db, User, Note, Payment
from sqlalchemy import func


def get_admin_stats():

    total_users = db.session.query(func.count(User.id)).scalar()

    pro_users = db.session.query(func.count(User.id))\
        .filter(User.plan == "pro").scalar()

    total_notes = db.session.query(func.count(Note.id)).scalar()

    total_revenue = db.session.query(
        func.coalesce(func.sum(Payment.amount), 0)
    ).scalar()

    return {
        "users": total_users,
        "pro_users": pro_users,
        "free_users": total_users - pro_users,
        "notes": total_notes,
        "revenue": total_revenue
    }
