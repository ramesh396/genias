from flask import Flask, render_template, request, Response, send_file
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
import uuid
import os
from authlib.integrations.flask_client import OAuth
from flask import session, redirect, url_for


app = Flask(__name__)

app.secret_key = "supersecretkey"  # change later

oauth = OAuth(app)

github = oauth.register(
    name="github",
    client_id=os.environ.get("GITHUB_CLIENT_ID"),
    client_secret=os.environ.get("GITHUB_CLIENT_SECRET"),
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email"},
)



# ---------------- HO
# 

@app.route("/")
def index():
    return render_template("index.html")

# ---------------- STREAM NOTES ----------------
@app.route("/stream", methods=["POST"])
def stream_notes():
    data = request.get_json()
    prompt = data.get("prompt", "")

    def generate():
        demo_text = f"""
Demo Notes (Cloud Ready)

Prompt:
{prompt}

This app is deployed successfully.
Cloud AI will be connected next.
"""
        for line in demo_text.split("\n"):
            yield line + "\n"

    return Response(generate(), mimetype="text/plain")


# ---------------- PDF DOWNLOAD ----------------
@app.route("/download", methods=["POST"])
def download_pdf():
    content = request.form.get("content")

    if not content:
        return "No content to download"

    filename = f"notes_{uuid.uuid4().hex}.pdf"
    filepath = filename

    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    for line in content.split("\n"):
        story.append(Paragraph(line, styles["Normal"]))

    doc.build(story)

    return send_file(filepath, as_attachment=True)


@app.route("/login")
def login():
    redirect_uri = url_for("callback", _external=True)
    return github.authorize_redirect(redirect_uri)

@app.route("/callback")
def callback():
    token = github.authorize_access_token()
    user = github.get("user").json()

    session["user"] = {
        "name": user.get("name"),
        "username": user.get("login"),
        "avatar": user.get("avatar_url")
    }

    return redirect("/")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")



if __name__ == "__main__":
    app.run(debug=True)
