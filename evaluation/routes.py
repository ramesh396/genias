from flask import Blueprint, request, session, redirect, render_template, current_app
from evaluation.utils import evaluate_answer_ai
from utils.db_helpers import get_user_plan, is_admin
from utils.security import verify_csrf

evaluation_bp = Blueprint("evaluation", __name__)


# ---------------- EVALUATION PAGE ----------------
@evaluation_bp.route("/evaluate")
def evaluate_page():

    if "user_id" not in session:
        return redirect("/")

    plan = get_user_plan(session["user_id"])

    if plan != "pro" and not is_admin():
        return render_template("evaluate_locked.html")

    return render_template("evaluate.html")


# ---------------- EVALUATE ANSWER ----------------
@evaluation_bp.route("/evaluate_answer", methods=["POST"])
def evaluate_answer():

    if "user_id" not in session:
        return "Unauthorized", 401

    verify_csrf()

    plan = get_user_plan(session["user_id"])
    if plan != "pro" and not is_admin():
        return "Upgrade to Pro to use Evaluation.", 403

    question = request.form.get("question", "").strip()
    answer = request.form.get("answer", "").strip()

    # 🔐 INPUT VALIDATION
    if not question or not answer:
        return "Question and answer required", 400

    if len(question) > 1000 or len(answer) > 3000:
        return "Input too long", 400

    # ---------- AI EVALUATION ----------
    try:
        output = evaluate_answer_ai(question, answer)
    except Exception:
        current_app.logger.exception("Evaluation AI failed")
        return "Evaluation service temporarily unavailable. Please try again.", 500

    return output
