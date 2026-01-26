from flask import Blueprint, render_template, session, redirect

pages_bp = Blueprint("pages_bp", __name__)


@pages_bp.route("/")
def landing():
    # If user already logged in, send directly to dashboard
    if "user_id" in session:
        return redirect("/dashboard")

    return render_template("landing.html")


@pages_bp.route("/upgrade")
def upgrade():
    # Only logged-in users can access upgrade page
    if "user_id" not in session:
        return redirect("/")

    # If already pro user, no need to show upgrade
    if session.get("plan") == "pro":
        return redirect("/dashboard")

    return render_template("upgrade.html")


@pages_bp.route("/pricing")
def pricing():
    # Simple alias route for upgrade page
    return redirect("/upgrade")


@pages_bp.route("/privacy")
def privacy():
    return render_template("privacy.html")


@pages_bp.route("/terms")
def terms():
    return render_template("terms.html")
