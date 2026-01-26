from models_pg import db, ChatSession, Chat


def create_new_session(user_id):
    """
    Always create a fresh chat session (like ChatGPT)
    """
    new_session = ChatSession(
        user_id=user_id,
        title="New Chat"
    )

    db.session.add(new_session)
    db.session.commit()

    return new_session.id


def get_or_create_session(user_id, session_id=None):
    """
    If a session_id is provided, use it.
    Otherwise create a brand new session.
    """

    if session_id:
        existing = ChatSession.query.filter_by(
            id=session_id,
            user_id=user_id
        ).first()

        if existing:
            return existing.id

    # No session provided → make new one
    return create_new_session(user_id)


def update_session_title(session_id, question):
    """
    Set chat title based on first message only
    """

    session = ChatSession.query.get(session_id)

    if not session:
        return

    # Update title ONLY if it is still default
    if session.title == "New Chat":

        # Make clean short title
        title = question.strip()

        title = title.replace("\n", " ")

        if len(title) > 40:
            title = title[:40] + "..."

        session.title = title
        db.session.commit()


def get_chat_context(user_id, session_id, limit=4):
    """
    Return last few messages for AI context
    """

    rows = Chat.query.filter_by(
        user_id=user_id,
        session_id=session_id
    ).order_by(Chat.id.desc()).limit(limit).all()

    rows = rows[::-1]  # keep correct order

    context = ""

    for r in rows:
        context += f"Student: {r.question}\n"
        context += f"Assistant: {r.answer}\n\n"

    return context


def list_user_sessions(user_id):
    """
    Return sessions in proper order for sidebar
    """

    sessions = ChatSession.query.filter_by(
        user_id=user_id
    ).order_by(ChatSession.id.desc()).all()

    return [
        {
            "id": s.id,
            "title": s.title or "New Chat"
        }
        for s in sessions
    ]
