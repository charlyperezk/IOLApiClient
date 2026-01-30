from __future__ import annotations

import json
import os
import random
import time
from typing import Any, Optional

import httpx


def _extract_text(response_json: dict[str, Any]) -> str:
    if "output_text" in response_json and isinstance(response_json["output_text"], str):
        return response_json["output_text"].strip()
    for item in response_json.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"}:
                text = content.get("text")
                if text:
                    return str(text).strip()
    return ""


def generate_daily_summary_text(
    metrics: dict[str, Any],
    *,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> str:
    api_key = api_key or os.environ["OPENAI_API_KEY"]
    model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    instructions = (
        "Eres un analista financiero conciso. Resume el dia en 6-10 lineas, "
        "sin consejos de inversion, sin inventar datos. Usa solo los datos provistos."
    )
    payload = {
        "model": model,
        "instructions": instructions,
        "input": f"Datos del reporte diario:\n{json.dumps(metrics, ensure_ascii=False, default=str)}",
        "max_output_tokens": 300,
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    with httpx.Client(timeout=20) as client:
        retries = int(os.getenv("OPENAI_RETRIES", "4"))
        base_delay = float(os.getenv("OPENAI_RETRY_BASE_DELAY", "0.8"))
        for attempt in range(retries + 1):
            response = client.post(
                "https://api.openai.com/v1/responses",
                json=payload,
                headers=headers,
            )
            if os.getenv("OPENAI_DEBUG", "0") in {"1", "true", "yes", "y", "on"}:
                rate_headers = {
                    key: value
                    for key, value in response.headers.items()
                    if key.lower().startswith("x-ratelimit")
                    or key.lower() in {"retry-after", "request-id", "x-request-id"}
                }
                print(
                    "openai_response",
                    {
                        "status_code": response.status_code,
                        "headers": rate_headers,
                        "body": response.text[:1000],
                    },
                )
            if response.status_code != 429:
                response.raise_for_status()
                data = response.json()
                break
            if attempt >= retries:
                response.raise_for_status()
            retry_after = response.headers.get("retry-after")
            if retry_after is not None:
                try:
                    delay = float(retry_after)
                except ValueError:
                    delay = base_delay * (2**attempt)
            else:
                delay = base_delay * (2**attempt)
            delay += random.uniform(0, 0.25 * delay)
            time.sleep(delay)
    text = _extract_text(data)
    if not text:
        raise RuntimeError("OpenAI response did not include output text.")
    return text
