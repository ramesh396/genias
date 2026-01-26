from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


# ---------------- USER MODEL ----------------
class User(db.Model):
    __tablename__ = "users"

    # --- EMAIL VERIFICATION ---
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    email_verification_token = db.Column(db.String(200), nullable=True)

# --- FORGOT PASSWORD ---
    reset_token = db.Column(db.String(200), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)


    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)

    password = db.Column(db.String(200), nullable=True)

    plan = db.Column(db.String(20), default="free", nullable=False, index=True)

    role = db.Column(db.String(20), default="user", nullable=False, index=True)

    created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    notes = db.relationship("Note", backref="user", lazy=True, cascade="all, delete-orphan")
    chats = db.relationship("Chat", backref="user", lazy=True, cascade="all, delete-orphan")
    sessions = db.relationship("ChatSession", backref="user", lazy=True, cascade="all, delete-orphan")
    tests = db.relationship("MemoryTest", backref="user", lazy=True, cascade="all, delete-orphan")
    payments = db.relationship("Payment", backref="user", lazy=True, cascade="all, delete-orphan")

    def is_admin(self):
        return self.role == "admin"


# ---------------- NOTES MODEL ----------------
class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    lesson = db.Column(db.String(200), index=True)
    content = db.Column(db.Text)

    created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)


# ---------------- PAYMENT MODEL ----------------
class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    payment_id = db.Column(db.String(120))
    order_id = db.Column(db.String(120))

    amount = db.Column(db.Integer)
    currency = db.Column(db.String(10))

    status = db.Column(db.String(50), default="created")

    created = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------- CHAT SESSION MODEL ----------------
class ChatSession(db.Model):
    __tablename__ = "chat_sessions"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    title = db.Column(db.String(200))

    created = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------- CHAT MODEL ----------------
class Chat(db.Model):
    __tablename__ = "chats"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)

    question = db.Column(db.Text)
    answer = db.Column(db.Text)

    created = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------- MEMORY TEST MODEL ----------------
class MemoryTest(db.Model):
    __tablename__ = "memory_tests"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    note_id = db.Column(db.Integer, db.ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)

    score = db.Column(db.Float)
    total = db.Column(db.Integer)
    percentage = db.Column(db.Float)

    created = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------- TUTOR SESSION MODEL ----------------
class TutorSession(db.Model):
    __tablename__ = "tutor_sessions"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    title = db.Column(db.String(200))

    created = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------- TUTOR MESSAGE MODEL ----------------
class TutorMessage(db.Model):
    __tablename__ = "tutor_messages"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey("tutor_sessions.id", ondelete="CASCADE"), nullable=False)

    role = db.Column(db.String(20))
    message = db.Column(db.Text)

    image_path = db.Column(db.String(300), nullable=True)

    created = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------- STUDENT PROGRESS MODEL ----------------
class StudentProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer)
    topic = db.Column(db.String(300))
    difficulty = db.Column(db.String(50))
    notes = db.Column(db.Text)

    last_question = db.Column(db.Text)
    language = db.Column(db.String(10))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
