from flask import Flask, session
from authlib.integrations.flask_client import OAuth
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# SQLAlchemy + Migrations
from flask_migrate import Migrate
from models_pg import db, User

# Blueprints
from payments.routes import payments_bp
from auth.routes import auth_bp
from admin.routes import admin_bp
from chat.routes import chat_bp
from memory.routes import memory_bp
from notes.routes import notes_bp
from evaluation.routes import evaluation_bp
from user.routes import user_bp
from pages.routes import pages_bp
from voice.routes import voice_bp
from stt.routes import stt_bp


from utils.security import generate_csrf
from tutor import tutor_bp


# ---------------- APP CONFIG ----------------
app = Flask(__name__)

app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_secret_key")

# ----------- POSTGRESQL CONFIGURATION (RENDER SAFE) -----------

db_url = os.getenv("DATABASE_URL")

if not db_url:
    raise RuntimeError("DATABASE_URL is not set in environment variables")

# SQLAlchemy requires postgresql:// not postgres://
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# Initialize DB
db.init_app(app)
migrate = Migrate(app, db)


# ---------------- REGISTER BLUEPRINTS ----------------
app.register_blueprint(payments_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(memory_bp)
app.register_blueprint(notes_bp)
app.register_blueprint(evaluation_bp)
app.register_blueprint(user_bp)
app.register_blueprint(pages_bp)
app.register_blueprint(tutor_bp)
app.register_blueprint(voice_bp)
app.register_blueprint(stt_bp)


# CSRF Token available in templates
app.jinja_env.globals["csrf_token"] = generate_csrf


# ---------------- USER CONTEXT PROCESSOR ----------------
@app.context_processor
def inject_user():
    """
    Makes user information automatically available
    in ALL templates
    """

    username = session.get("username")
    plan = "free"
    role = "user"

    if "user_id" in session:
        user = db.session.get(User, session["user_id"])
        if user:
            plan = user.plan
            role = user.role

            # Keep session synced with database
            session["plan"] = user.plan
            session["role"] = user.role

    return dict(
        username=username,
        plan=plan,
        role=role
    )


# ---------------- GOOGLE AUTH (Single Instance) ----------------
app.config["GOOGLE_CLIENT_ID"] = os.getenv("GOOGLE_CLIENT_ID")
app.config["GOOGLE_CLIENT_SECRET"] = os.getenv("GOOGLE_CLIENT_SECRET")

oauth = OAuth(app)

oauth.register(
    name="google",
    client_id=app.config["GOOGLE_CLIENT_ID"],
    client_secret=app.config["GOOGLE_CLIENT_SECRET"],
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"}
)


# ---------------- CREATE TABLES (Safety) ----------------
with app.app_context():
    db.create_all()


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
