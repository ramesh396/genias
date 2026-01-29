from flask import (
    Blueprint, request, session, redirect,
    render_template, url_for, current_app
)

from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets

from models_pg import db, User
from utils.security import verify_csrf

# ✅ IMPORT SHARED OAUTH INSTANCE
from extensions import oauth


auth_bp = Blueprint("auth", __name__)

# =================================================
# REGISTER
# =================================================
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("index.html")

    verify_csrf()

    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "").strip()

    if not username or not email or not password:
        return "All fields required", 400

    if User.query.filter_by(email=email).first():
        return "Email already registered", 400

    user = User(
        username=username,
        email=email,
        password=generate_password_hash(password),
        email_verified=True,  # TEMP
        role="user",
        plan="free",
        created=datetime.utcnow()
    )

    db.session.add(user)
    db.session.commit()

    return redirect("/login")


# =================================================
# LOGIN
# =================================================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("index.html")

    verify_csrf()

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "").strip()

    user = User.query.filter_by(email=email).first()

    if not user or not user.password:
        return "Invalid credentials", 401

    if not check_password_hash(user.password, password):
        return "Invalid credentials", 401

    session.clear()
    session.update({
        "user_id": user.id,
        "username": user.username,
        "plan": user.plan,
        "role": user.role
    })

    return redirect("/dashboard")


# =================================================
# GOOGLE LOGIN
# =================================================
@auth_bp.route("/login/google")
def google_login():
    redirect_uri = url_for("auth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


# =================================================
# GOOGLE CALLBACK
# =================================================
@auth_bp.route("/login/google/callback")
def google_callback():

    token = oauth.google.authorize_access_token()

    user_info = oauth.google.get(
        "https://openidconnect.googleapis.com/v1/userinfo"
    ).json()

    email = user_info.get("email")
    name = user_info.get("name") or email.split("@")[0]

    user = User.query.filter_by(email=email).first()

    if not user:
        user = User(
            username=name,
            email=email,
            password=None,
            email_verified=True,
            role="user",
            plan="free",
            created=datetime.utcnow()
        )
        db.session.add(user)
        db.session.commit()

    session.clear()
    session.update({
        "user_id": user.id,
        "username": user.username,
        "plan": user.plan,
        "role": user.role
    })

    return redirect("/dashboard")
