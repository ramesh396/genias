from werkzeug.security import generate_password_hash, check_password_hash
from models_pg import db, User


def create_user(email, password):
    username = email.split("@")[0]

    existing = User.query.filter_by(email=email).first()
    if existing:
        raise Exception("User already exists")

    user = User(
        username=username,
        email=email,
        password=generate_password_hash(password),
        plan="free"
    )

    db.session.add(user)
    db.session.commit()

    return user


def validate_user(email, password):
    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password, password):
        return user

    return None


def get_or_create_google_user(email):
    username = email.split("@")[0]

    user = User.query.filter_by(email=email).first()

    if not user:
        user = User(
            username=username,
            email=email,
            password="GOOGLE",
            plan="free"
        )

        db.session.add(user)
        db.session.commit()

    return user
