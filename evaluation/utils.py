from ai.groq import groq_generate


def evaluate_answer_ai(question, answer):
    if not question.strip() or not answer.strip():
        return "Question and answer cannot be empty."

    prompt = f"""
You are a strict and experienced exam paper evaluator.

FOLLOW THESE RULES STRICTLY:
- Evaluate like a real teacher
- Be unbiased and fair
- Focus on exam marks
- No unnecessary extra text
- Clear structured response
- Simple professional language

REQUIRED RESPONSE FORMAT ONLY:

SCORE:
(Give marks out of 10)

STRENGTHS:
- Point 1
- Point 2

WEAKNESSES:
- Point 1
- Point 2

IMPROVEMENT:
- Practical steps to improve

MODEL ANSWER:
(Write a short, ideal exam-ready answer)

----------------------------------------

QUESTION:
{question}

STUDENT ANSWER:
{answer}
"""

    try:
        return groq_generate(
            prompt=prompt,
            max_tokens=450,
            temperature=0.15
        )
    except Exception as e:
        print("AI Evaluation Error:", e)
        return "AI evaluation service unavailable. Please try again later."
