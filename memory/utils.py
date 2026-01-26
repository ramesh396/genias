from ai.groq import groq_generate


def evaluate_memory_answers(questions, answers):
    score = 0.0
    total = len(questions)

    for q, ans in zip(questions, answers):
        if not ans:
            continue

        prompt = f"""
You are evaluating an ACTIVE RECALL answer.

RULES:
- Respond with ONLY ONE NUMBER
- Allowed values: 1, 0.5, 0
- No explanation, no text

SCORING:
1   = fully correct
0.5 = partially correct
0   = wrong or irrelevant

QUESTION:
{q}

STUDENT ANSWER:
{ans}

SCORE:
"""

        result = groq_generate(
            prompt=prompt,
            max_tokens=5,
            temperature=0
        )

        try:
            score += float(result.strip())
        except:
            pass

    percentage = round((score / total) * 100, 2) if total else 0

    return score, total, percentage
