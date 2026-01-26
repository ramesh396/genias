from ai.groq import groq_generate


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

    base_instruction = f"""
User has pasted study material.

TASK:
Convert the following lesson text into well-structured, exam-friendly notes.

TEXT TO CONVERT:
{pasted_text}

"""

    if mode == "board":
        return base_instruction + """
FORMAT REQUIRED:

DEFINITION:
KEY POINTS:
EXAM POINTS:
EXAMPLE:
""", 0.16, 450

    if mode == "college":
        return base_instruction + """
FORMAT REQUIRED:

DEFINITION:
KEY CONCEPTS:
IMPORTANT FORMULAS:
EXAM POINTS:
REAL WORLD EXAMPLE:
""", 0.18, 450

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

FORMAT:

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

FORMAT:
DEFINITION:
KEY POINTS:
EXAM POINTS:
EXAMPLE:

TOPIC:
{lesson}
""", 0.15, 320

    if mode == "college":
        return f"""
You are a university exam answer writer.

FORMAT:
DEFINITION:
KEY POINTS:
EXAM POINTS:
EXAMPLE:

TOPIC:
{lesson}
""", 0.18, 320

    if mode == "short":
        return f"""
Create ultra-short revision notes.

FORMAT:
KEY POINTS:
- Point 1
- Point 2
- Point 3
- Point 4
- Point 5

TOPIC:
{lesson}
""", 0.12, 250

    if mode == "mcq":
        return f"""
Create exam-level MCQs.

FORMAT:
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


def poetry_prompt(lesson: str) -> tuple[str, float, int]:
    prompt = f"""
You are an English literature exam specialist.

TASK:
Write exam-oriented poetry notes.

FORMAT:
POET:
CONTEXT:
SUMMARY:
THEMES:
LITERARY DEVICES:
TONE / MOOD:
EXAM POINTS:

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

    # ---------- NEW: PASTED TEXT MODE ----------
    elif pasted_mode:
        try:
            prompt, temperature, max_tokens = build_paste_prompt(user_prompt, mode)
        except ValueError:
            return "Invalid generation mode."

    # ---------- NORMAL TOPIC MODE ----------
    else:
        try:
            prompt, temperature, max_tokens = build_prompt(lesson, mode)
        except ValueError:
            return "Invalid generation mode."

        # attach extra instruction if small
        if user_prompt and user_prompt.strip():
            prompt += f"\nUSER INSTRUCTION:\n{user_prompt.strip()}\n"

    max_tokens = min(max_tokens, base_max)

    return groq_generate(
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        history=history
    )
