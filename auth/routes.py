from flask import (
    Blueprint, request, session, redirect,
    render_template, url_for, current_app
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets

from models_pg import db, User
from utils.security import verify_csrf

from authlib.integrations.flask_client import OAuth

auth_bp = Blueprint("auth", __name__)
oauth = OAuth()

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

    token = secrets.token_urlsafe(32)

    user = User(
        username=username,
        email=email,
        password=generate_password_hash(password),
        email_verified=True,  # TEMP
        email_verification_token=None,
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
# FORGOT PASSWORD (✅ FIXED)
# =================================================
@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "GET":
        return render_template("forgot_password.html")

    verify_csrf()

    email = request.form.get("email", "").strip().lower()

    print("FORGOT EMAIL:", email)

    user = User.query.filter_by(email=email).first()

    print("FOUND USER:", user.email if user else None)

    if user:
        token = secrets.token_urlsafe(32)

        user.reset_token = token
        user.reset_token_expiry = datetime.utcnow() + timedelta(minutes=30)
        db.session.commit()

        reset_link = url_for(
            "auth.reset_password",
            token=token,
            _external=True
        )

        print("RESET LINK:", reset_link)

    return redirect("/login")


# =================================================
# RESET PASSWORD
# =================================================
@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):

    user = User.query.filter_by(reset_token=token).first()

    if not user or user.reset_token_expiry < datetime.utcnow():
        return "Invalid or expired reset link", 400

    if request.method == "POST":
        verify_csrf()

        new_password = request.form.get("password", "").strip()
        confirm = request.form.get("confirm_password", "").strip()

        if not new_password or new_password != confirm:
            return "Passwords do not match", 400

        user.password = generate_password_hash(new_password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()

        return redirect("/login")

    return render_template("reset_password.html")


# =================================================
# LOGOUT
# =================================================
@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# =================================================
# GOOGLE OAUTH INIT
# =================================================
@auth_bp.record_once
def init_oauth(state):
    app = state.app
    oauth.init_app(app)

    client_id = app.config.get("GOOGLE_CLIENT_ID")
    client_secret = app.config.get("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret:
        app.logger.warning("Google OAuth not configured")
        return

    oauth.register(
        name="google",
        client_id=client_id,
        client_secret=client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"}
    )


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
