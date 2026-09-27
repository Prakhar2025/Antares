"""Bedrock Converse wrapper: strict-JSON voting for the quorum.

One function, one contract: send a system and user text, get a parsed
JSON object and the token usage back. Malformed model output raises
ModelOutputError; the quorum decides what that means (one retry, then
an abstain with a named finding). Models never see raw unframed text:
the caller embeds content inside the data framing of a fixed template.
"""

from __future__ import annotations

import json
from typing import Any


class ModelOutputError(ValueError):
    """The model did not return parseable JSON."""


def extract_json(text: str) -> dict[str, Any]:
    """Pull the first balanced JSON object out of model text."""
    start = text.find("{")
    if start == -1:
        raise ModelOutputError("no JSON object in model output")
    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(text)):
        ch = text[index]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
        elif ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start : index + 1]
                try:
                    parsed: dict[str, Any] = json.loads(candidate)
                    return parsed
                except json.JSONDecodeError as error:
                    raise ModelOutputError(f"invalid JSON in model output: {error}") from None
    raise ModelOutputError("unbalanced JSON in model output")


def converse_text(
    client: Any,
    model_id: str,
    system: str,
    user: str,
    max_tokens: int = 400,
    temperature: float = 0.0,
) -> tuple[str, dict[str, int]]:
    """Invoke one model via Converse and return (raw_text, token_usage)."""
    response = client.converse(
        modelId=model_id,
        system=[{"text": system}],
        messages=[{"role": "user", "content": [{"text": user}]}],
        inferenceConfig={"temperature": temperature, "maxTokens": max_tokens},
    )
    content = response["output"]["message"]["content"]
    text = "".join(part.get("text", "") for part in content)
    usage = response.get("usage", {})
    return text, {
        "input": int(usage.get("inputTokens", 0)),
        "output": int(usage.get("outputTokens", 0)),
    }


def converse_json(
    client: Any,
    model_id: str,
    system: str,
    user: str,
    max_tokens: int = 400,
    temperature: float = 0.0,
) -> tuple[dict[str, Any], dict[str, int]]:
    """Invoke one model and return (parsed_json, token_usage)."""
    text, usage = converse_text(client, model_id, system, user, max_tokens, temperature)
    return extract_json(text), usage
