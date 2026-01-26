import requests
import os


def groq_generate(prompt, max_tokens=500, temperature=0.2, history=None):
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return "AI service is not configured. Contact administrator."

    if not prompt or prompt.strip() == "":
        return "No input provided."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # ----- BUILD MESSAGES WITH MEMORY -----
    messages = [
        {
            "role": "system",
            "content": """
You are a friendly, patient, human-like AI Tutor.

Behavior Rules:
- Talk like a real teacher
- Remember previous conversation
- Understand follow-up questions
- Be conversational and natural
- Ask small questions back
- Encourage the student
- Explain in simple language
- Never act robotic
"""
        }
    ]

    # Add conversation history if available
    if history:
        messages.extend(history)

    # Add current user question
    messages.append({
        "role": "user",
        "content": prompt
    })

    # ----- FINAL API PAYLOAD -----
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 429:
            return "AI daily free limit reached. Try again later."

        if response.status_code == 401:
            return "Invalid AI API key configuration."

        if response.status_code != 200:
            return f"AI error: {response.status_code}"

        data = response.json()

        return data.get("choices", [{}])[0].get("message", {}).get("content", "AI returned empty response.")

    except requests.exceptions.Timeout:
        return "AI service timeout. Please try again."

    except requests.exceptions.ConnectionError:
        return "Cannot connect to AI service."

    except Exception as e:
        return "AI service unavailable."
