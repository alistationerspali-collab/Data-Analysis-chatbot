"""Wrapper around the Groq SDK for chat completions."""
import json
from groq import Groq
from app.config import settings

client = Groq(api_key=settings.groq_api_key)


def get_completion(messages: list[dict], response_format: str = None) -> dict | str:
    kwargs = {
        "model": settings.groq_model,
        "messages": messages,
        "temperature": 0,
    }
    if response_format == "json":
        kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**kwargs)
    content = response.choices[0].message.content

    if response_format == "json":
        content = content.strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(content)

    return content