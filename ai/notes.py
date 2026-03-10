from ai.groq import groq_generate


# ================= SMART NOTES SYSTEM =================

SMART_NOTES_RULES = """
You are an expert academic teacher.

The student may only provide a lesson, chapter, or topic name.

You must automatically:
- Identify the subject (science, history, literature, etc.)
- Identify the likely academic level
- Understand if it is a poem, story, concept, or theory.

Do NOT ask the student for board, class, or exam type.

Write FULL exam-ready notes.

NOTES STRUCTURE:

TITLE

1. Introduction
Explain the topic clearly.

2. Background / Context
Explain where the topic comes from.

3. Detailed Explanation
Explain deeply with examples.

4. Important Concepts / Key Points

5. Analysis or Examples
• For literature → characters, themes, message  
• For science → process, explanation  
• For history → causes and effects

6. Quick Revision Summary

7. Possible Exam Questions
• 2 mark questions
• 5 mark questions
• 10 mark questions

Write at least 900 words if possible.
"""


# ================= POEM DETECTION =================

def is_poem_topic(text: str):

    if not text:
        return False

    text = text.lower()

    poem_keywords = [
        "poem", "poetry", "sonnet", "ode", "ballad"
    ]

    known_poems = [
        "london",
        "daffodils",
        "road not taken",
        "nightingale",
        "sonnet"
    ]

    return any(k in text for k in poem_keywords) or any(p in text for p in known_poems)


# ================= POETRY PROMPT =================

def poetry_prompt(lesson: str):

    prompt = f"""
You are an English literature expert.

Write exam-ready poetry notes.

FORMAT:

TITLE
POET
CONTEXT
SUMMARY
THEMES
LITERARY DEVICES
TONE / MOOD
MESSAGE
IMPORTANT LINES
EXAM QUESTIONS

POEM:
{lesson}
"""

    return prompt, 0.22, 1200


# ================= NORMAL NOTES PROMPT =================

def notes_prompt(lesson: str, user_prompt: str = ""):

    extra = ""

    if user_prompt:
        extra = f"""

Additional study material provided by the student:
{user_prompt}

Use this material to improve the notes if relevant.
"""

    prompt = f"""
{SMART_NOTES_RULES}

TOPIC:
{lesson}

{extra}
"""

    return prompt, 0.25, 1200


# ================= MCQ PROMPT =================

def mcq_prompt(lesson: str):

    prompt = f"""
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
"""

    return prompt, 0.20, 800


# ================= TUTOR CHAT =================

def tutor_prompt(user_text: str):

    prompt = f"""
You are a friendly teacher.

Explain clearly in simple language.

End with:
"Did you understand? Should I explain differently?"

STUDENT QUESTION:
{user_text}
"""

    return prompt, 0.35, 1000


# ================= MAIN GENERATOR =================

def generate_notes_with_groq(
    lesson: str,
    user_prompt: str = "",
    mode: str = "notes",
    history=None,
    plan: str = "free"
):

    if not lesson or lesson.strip() == "":
        return "Please enter a topic."

    mode = mode.lower()

    base_tokens = 900 if plan == "free" else 1600

    # -------- Tutor Mode --------
    if mode == "tutor":
        prompt, temperature, max_tokens = tutor_prompt(lesson)

    # -------- MCQ Mode --------
    elif mode == "mcq":
        prompt, temperature, max_tokens = mcq_prompt(lesson)

    # -------- Poetry Detection --------
    elif is_poem_topic(lesson):
        prompt, temperature, max_tokens = poetry_prompt(lesson)

    # -------- Default Notes --------
    else:
        prompt, temperature, max_tokens = notes_prompt(lesson, user_prompt)

    max_tokens = min(max_tokens, base_tokens)

    return groq_generate(
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        history=history
    )