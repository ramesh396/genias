from flask import session, request, abort
import secrets


def generate_csrf():
    """
    Generate CSRF token if not present in session
    """
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(32)   # stronger token
    return session["_csrf_token"]


def verify_csrf():
    """
    Verify CSRF token from form submission
    """
    token = request.form.get("csrf_token")

    if not token:
        abort(403, description="Missing CSRF token")

    if token != session.get("_csrf_token"):
        abort(403, description="Invalid CSRF token")

