"""Ollama quickstart examples for this repo.

Usage:
  python ollama_quickstart.py --mode text
  python ollama_quickstart.py --mode vision --image ./image.jpg
  python ollama_quickstart.py --mode tool

Before running:
  ollama serve
  ollama pull qwen3.5:cloud
  ollama pull gemma4

Recommended models for Apple Silicon:
  - vision: gemma4
  - all-in-one recommended: qwen3.5:cloud
"""

import argparse
from ollama import chat

RECOMMENDED_MODELS = {
    "vision": "gemma4",
    "thinking": "qwen3.5:cloud",
    "cloud": "qwen3.5:cloud",
}


def summarize_text(text: str, model: str = RECOMMENDED_MODELS["thinking"]) -> str:
    response = chat(
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


def describe_image(image_path: str, prompt: str = "Describe this image and explain what you see.", model: str = RECOMMENDED_MODELS["vision"]) -> str:
    response = chat(
        model=model,
        messages=[
            {"role": "user", "content": prompt, "images": [image_path]},
        ],
        stream=False,
    )
    return response.message.content


def tool_call_example(model: str = RECOMMENDED_MODELS["thinking"]) -> str:
    def get_temperature(city: str) -> str:
        temperatures = {
            "New York": "22°C",
            "London": "15°C",
            "Tokyo": "18°C",
        }
        return temperatures.get(city, "Unknown")

    messages = [{"role": "user", "content": "What is the temperature in New York?"}]
    response = chat(model=model, messages=messages, tools=[get_temperature], think=True, stream=False)

    if not getattr(response.message, "tool_calls", None):
        return response.message.content

    call = response.message.tool_calls[0]
    result = get_temperature(**call.function.arguments)
    messages.append({"role": "tool", "tool_name": call.function.name, "content": result})

    follow_up = chat(model=model, messages=messages, tools=[get_temperature], think=True, stream=False)
    return follow_up.message.content


def main() -> None:
    parser = argparse.ArgumentParser(description="Ollama quickstart helper")
    parser.add_argument("--mode", choices=["text", "vision", "tool"], default="text")
    parser.add_argument("--image", help="Image path for vision mode")
    parser.add_argument("--prompt", help="Prompt text for vision mode")
    args = parser.parse_args()

    if args.mode == "text":
        sample_text = (
            "Python is a programming language. "
            "It is used for AI, machine learning, web development and automation."
        )
        print("=== Summarize text ===")
        print(summarize_text(sample_text))

    elif args.mode == "vision":
        if not args.image:
            raise SystemExit("Error: --image is required for vision mode")
        print("=== Describe image ===")
        print(describe_image(args.image, prompt=args.prompt or "Describe this image and explain what you see."))

    elif args.mode == "tool":
        print("=== Tool-calling demo ===")
        print(tool_call_example())


if __name__ == "__main__":
    main()
