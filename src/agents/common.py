from __future__ import annotations

import hashlib
import json
from typing import TypeVar

from pydantic import BaseModel, ValidationError


class AgentOutputError(RuntimeError):
    pass


T = TypeVar("T", bound=BaseModel)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def call_agent(
    *,
    model: str,
    system_prompt: str,
    user_prompt: str,
    output_model: type[T],
    max_retries: int = 2,
) -> T:
    """Call an Ollama model in JSON mode and validate its output with Pydantic."""

    try:
        import ollama
    except Exception as e:  # pragma: no cover
        raise AgentOutputError(
            "Ollama client not available. Install deps and ensure Ollama is running."
        ) from e

    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        response = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            options={"format": "json"},
        )

        raw = response["message"]["content"]
        try:
            return output_model.model_validate(json.loads(raw))
        except (ValidationError, json.JSONDecodeError) as e:
            last_error = e
            if attempt >= max_retries:
                raise AgentOutputError(
                    f"Agent output validation failed after {max_retries} retries: {e}"
                ) from e

    raise AgentOutputError(f"Agent output validation failed: {last_error}")
