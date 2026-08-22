from ollama import Client
from config import Config

_ollama_client = Client(host=Config.OLLAMA_HOST)


def summarize(text: str, model: str = Config.OLLAMA_MODEL) -> str:
    """Generate a concise summary of multiple emails using Ollama."""

    prompt = f"""
You are an email summarization assistant.

Summarize the emails below concisely.

For EACH email provide:
- Sender:
- Subject:
- Summary: 1-2 short sentences
- Action Required: Yes/No, followed by the action if needed

Rules:
- Ignore advertisements and promotional emails unless they contain important information.
- Do not repeat the email body.
- Do not add information that is not present in the emails.
- Keep the entire response under 500 words.
- Return ONLY the summary.
- Do NOT provide reasoning or a thinking process.
- Do NOT analyze the instructions.
- Start directly with "Sender:".

Emails:
{text}
"""

    response = _ollama_client.chat(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        think=False,
        options={
            "num_predict": 300,
            "temperature": 0.2,
        },
        stream=False,
    )

    content = response.message.content

    if not content:
        raise RuntimeError("Ollama returned an empty summary.")

    return content.strip()