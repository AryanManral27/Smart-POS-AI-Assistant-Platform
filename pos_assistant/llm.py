from __future__ import annotations

import json
import re
from typing import Any, TypeVar

from openai import OpenAI

from pos_assistant.config import settings

T = TypeVar("T")


def get_client() -> OpenAI | None:
    key = (settings.openrouter_api_key or "").strip()
    if not key:
        return None
    # Avoid hanging the whole /insights request if the provider is slow or unreachable
    return OpenAI(api_key=key, base_url=settings.openrouter_base_url, timeout=45.0)


def _extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        return json.loads(m.group())
    raise ValueError("Model did not return valid JSON")


def chat_json(system: str, user: str) -> dict[str, Any]:
    client = get_client()
    if client is None:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    resp = client.chat.completions.create(
        model=settings.openrouter_model,
        temperature=0.3,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    content = resp.choices[0].message.content or "{}"
    return _extract_json_object(content)


def chat_text(system: str, user: str) -> str:
    client = get_client()
    if client is None:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    resp = client.chat.completions.create(
        model=settings.openrouter_model,
        temperature=0.4,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return (resp.choices[0].message.content or "").strip()
