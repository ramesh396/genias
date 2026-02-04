from ai.groq import groq_generate


# ===================== CHANGE A: SYLLABUS_BLOCK (prepended to every prompt) =====================
# This block is intentionally strict to prevent hallucinations and keep outputs syllabus-aligned.
SYLLABUS_BLOCK = """
SYLLABUS ALIGNMENT & EXAM OUTPUT RULES (STRICT)

SCOPE NOTE:
- If the prompt is clearly in "tutor / explain like a teacher" mode, follow the tutor instructions for tone and interaction.
- Otherwise (notes/MCQs/summaries), follow ALL rules below strictly.

1) DO NOT GUESS / DO NOT INVENT:
- Do not add facts, names, dates, examples, interpretations, or definitions that are not explicitly in the user's syllabus/textbook/notes.
- For literature: do not guess the author/poet or line-by-line meanings if not provided in the syllabus/text.
- If the syllabus/text is missing or unclear, ask for the missing details and STOP. Do not "fill in" from general knowledge.

2) REQUIRED CONTEXT CHECK (ask if missing):
Before writing notes, confirm you know ALL of:
- Board/University (e.g., CBSE/ICSE/State Board/University name)
- Class/Grade OR Semester/Year
- Subject
- Chapter/Unit/Poem/Prose title (exact)
If any are missing, respond with ONLY:
MISSING INFO:
- ...
Please provide the missing items (or paste the official syllabus lines / textbook headings).

3) OUTPUT MUST BE EXAM-FOCUSED & STRUCTURED (NOT ESSAYS):
- Output only the requested structured notes (no greetings, no filler, no long paragraphs).
- Use bullet points under every heading; keep sentences short and exam-oriented.
- Keep each section concise (typically 3-7 bullets). No essay-style paragraphs.
- Stay strictly within syllabus boundaries.
"""
# =================== END CHANGE A ===================


def is_poem_topic(text: str) -> bool:
    if not text:
        return False

    text = text.lower()

    poem_keywords = [
        "poem", "poetry", "sonnet", "ode", "ballad",
        "by william blake", "by wordsworth", "by keats",
        "by shelley", "by robert frost", "by yeats"
    ]

    known_poems = [
        "london",
        "the daffodils",
        "the road not taken",
        "ode to a nightingale",
        "sonnet 18"
    ]

    return any(k in text for k in poem_keywords) or any(p in text for p in known_poems)


# ---------- NEW FUNCTION FOR PASTED LESSON MODE ----------
def build_paste_prompt(pasted_text: str, mode: str) -> tuple[str, float, int]:
    mode = mode.lower()

    base_instruction = f"""
User has pasted study material.

TASK:
Convert the following lesson text into STRICT syllabus-aligned, exam-focused notes.

STRICT RULES:
- Use ONLY the pasted text. Do not introduce outside information.
- Preserve the topic order and headings as they appear in the pasted text.
- Do not guess missing details; ask for missing syllabus context if needed.

TEXT TO CONVERT:
{pasted_text}

"""

    if mode == "board":
        return base_instruction + """
OUTPUT FORMAT (STRICT):
TITLE:
1) Key Concepts (preserve text order)
2) Important Definitions (preserve text order)
3) Explanation in Simple Language (preserve text order)
4) Diagrams / Processes (text description, preserve text order)
5) Quick Revision Box
6) Possible Exam Questions
""", 0.16, 450

    if mode == "college":
        return base_instruction + """
OUTPUT FORMAT (STRICT):
TITLE:
1) Key Concepts (preserve text order)
2) Important Definitions (preserve text order)
3) Explanation in Simple Language (preserve text order)
4) Diagrams / Processes (text description, preserve text order)
5) Quick Revision Box
6) Possible Exam Questions
""", 0.18, 450

    # ===================== CHANGE C/E: English prose in pasted-text mode =====================
    if mode == "english":
        return base_instruction + """
OUTPUT FORMAT (STRICT - PROSE CHAPTER):
TITLE:
AUTHOR:
SETTING:
CHARACTERS:
SUMMARY (bullets, preserve text order):
THEMES:
LITERARY DEVICES:
MESSAGE / MORAL:
EXAM QUESTIONS:
""", 0.20, 550
    # =================== END CHANGE C/E ===================

    if mode == "short":
        return base_instruction + """
FORMAT REQUIRED:

ULTRA SHORT NOTES:
- point 1
- point 2
- point 3
- point 4
- point 5
""", 0.12, 350

    if mode == "mcq":
        return base_instruction + """
Create MCQs directly from the given text.

STRICT RULES:
- Questions and answers must be derived ONLY from the pasted text.
- Do not add outside facts or examples.

FORMAT (STRICT):

1. Question?
A)
B)
C)
D)
Answer:
""", 0.10, 500

    raise ValueError("Invalid mode selected")


# ---------- EXISTING TOPIC MODE PROMPT ----------
def build_prompt(lesson: str, mode: str) -> tuple[str, float, int]:
    mode = mode.lower()

    if mode == "board":
        return f"""
You are an NCERT board-exam answer writer.

OUTPUT FORMAT (STRICT):
TITLE:
1) Key Concepts
2) Important Definitions
3) Explanation in Simple Language
4) Diagrams / Processes (text description)
5) Quick Revision Box
6) Possible Exam Questions

TOPIC:
{lesson}
""", 0.15, 320

    if mode == "college":
        return f"""
You are a university exam answer writer.

OUTPUT FORMAT (STRICT):
TITLE:
1) Key Concepts
2) Important Definitions
3) Explanation in Simple Language
4) Diagrams / Processes (text description)
5) Quick Revision Box
6) Possible Exam Questions

TOPIC:
{lesson}
""", 0.18, 320

    if mode == "short":
        return f"""
Create ultra-short revision notes.

OUTPUT FORMAT (STRICT):
TITLE:
QUICK REVISION BOX:
- Point 1
- Point 2
- Point 3
- Point 4
- Point 5
POSSIBLE EXAM QUESTIONS:
- Question 1
- Question 2

TOPIC:
{lesson}
""", 0.12, 250

    if mode == "mcq":
        return f"""
Create exam-level MCQs.

FORMAT (STRICT):
1. Question?
A)
B)
C)
D)
Answer:

TOPIC:
{lesson}
""", 0.10, 400

    raise ValueError("Invalid mode selected")


# ===================== CHANGE C: New prose_prompt() for English prose chapters =====================
def prose_prompt(lesson: str) -> tuple[str, float, int]:
    prompt = f"""
You are an English literature exam specialist.

TASK:
Write STRICT syllabus-aligned, exam-oriented notes for an English PROSE chapter (not poetry).
Avoid science-style "definition dumping". Focus on plot, characters, themes, and devices.

OUTPUT FORMAT (STRICT):
TITLE:
AUTHOR:
SETTING:
CHARACTERS:
SUMMARY (bullets):
THEMES:
LITERARY DEVICES:
MESSAGE / MORAL:
EXAM QUESTIONS:

PROSE CHAPTER:
{lesson}
"""
    return prompt, 0.22, 550
# =================== END CHANGE C ===================


def poetry_prompt(lesson: str) -> tuple[str, float, int]:
    prompt = f"""
You are an English literature exam specialist.

TASK:
Write STRICT syllabus-aligned, exam-oriented poetry notes (no guessing, no outside lines/quotes).

OUTPUT FORMAT (STRICT):
TITLE:
POET:
CONTEXT / BACKGROUND (only if in syllabus/text):
SUMMARY (bullets):
THEMES:
LITERARY DEVICES (with brief effect):
TONE / MOOD:
QUICK REVISION BOX:
POSSIBLE EXAM QUESTIONS:

POEM:
{lesson}
"""
    return prompt, 0.22, 500


# ----------------- TUTOR MODE (UNCHANGED) -----------------
def tutor_chat_prompt(user_text: str) -> tuple[str, float, int]:
    prompt = f"""
YOU ARE A REAL HUMAN-LIKE TEACHER.

Explain in simple friendly style.

Always end with:
"Did you understand? Shall I explain in another way?"

STUDENT INPUT:
{user_text}
"""

    return prompt, 0.35, 700


# ---------------- MAIN GENERATOR FUNCTION (MODIFIED) -----------------
def generate_notes_with_groq(
    lesson: str,
    mode: str = "board",
    user_prompt: str = "",
    plan: str = "free",
    history=None
):
    if not lesson or lesson.strip() == "":
        return "Please enter a valid topic."

    base_max = 320 if plan == "free" else 800
    mode = mode.lower()

    # ---------- DETECT IF USER PASTED LARGE TEXT ----------
    pasted_mode = False
    if user_prompt and len(user_prompt.strip()) > 80:
        pasted_mode = True

    # ---------- TUTOR MODE ----------
    if mode == "tutor":
        prompt, temperature, max_tokens = tutor_chat_prompt(lesson)

    # ---------- POETRY MODE ----------
    elif is_poem_topic(lesson):
        prompt, temperature, max_tokens = poetry_prompt(lesson)

    # ---------- PASTED TEXT MODE ----------
    elif pasted_mode:
        try:
            prompt, temperature, max_tokens = build_paste_prompt(user_prompt, mode)
        except ValueError:
            return "Invalid generation mode."

    # ---------- NORMAL TOPIC MODE ----------
    else:
        # ===================== CHANGE F: prose_prompt for English prose chapters =====================
        if mode == "english":
            prompt, temperature, max_tokens = prose_prompt(lesson)
        else:
            try:
                prompt, temperature, max_tokens = build_prompt(lesson, mode)
            except ValueError:
                return "Invalid generation mode."
        # =================== END CHANGE F ===================

        # attach extra instruction if small
        if user_prompt and user_prompt.strip():
            prompt += f"\nUSER INSTRUCTION:\n{user_prompt.strip()}\n"

    max_tokens = min(max_tokens, base_max)

    # ===================== CHANGE F: Prefix every prompt with SYLLABUS_BLOCK =====================
    prompt = f"{SYLLABUS_BLOCK}\n{prompt}"
    # =================== END CHANGE F ===================

    return groq_generate(
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        history=history
    )

