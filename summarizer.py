from ollama import Client
from config import Config

_ollama_client = Client(host=Config.OLLAMA_HOST)


def summarize(text: str, model: str = "qwen3.5:cloud") -> str:
    response = _ollama_client.chat(
        model=model,
        messages=[
            {
                "role": "user",
                "content": f"Summarize this text:\n{text}",
            }
        ],
        think=True,
        stream=False,
    )

    return response.message.content
