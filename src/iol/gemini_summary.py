from __future__ import annotations

import json
import os
import random
import time
from typing import Any, Optional

import httpx


def _extract_text(response_json: dict[str, Any]) -> str:
    candidates = response_json.get("candidates") or []
    if not candidates:
        return ""
    content = candidates[0].get("content") or {}
    parts = content.get("parts") or []
    for part in parts:
        text = part.get("text")
        if text:
            return str(text).strip()
    return ""


def generate_daily_summary_text(
    metrics: dict[str, Any],
    *,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> str:
    api_key = api_key or os.environ["GEMINI_API_KEY"]
    model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    instructions = (
        "Eres un analista financiero conciso. Resume el dia en 6-10 lineas, "
        "sin consejos de inversion, sin inventar datos. Usa solo los datos provistos."
    )
    prompt = (
        f"{instructions}\n\nDatos del reporte diario:\n"
        f"{json.dumps(metrics, ensure_ascii=False, default=str)}"
    )
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ]
    }
    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    with httpx.Client(timeout=20) as client:
        retries = int(os.getenv("GEMINI_RETRIES", "4"))
        base_delay = float(os.getenv("GEMINI_RETRY_BASE_DELAY", "0.8"))
        for attempt in range(retries + 1):
            response = client.post(url, json=payload, headers=headers)
            if os.getenv("GEMINI_DEBUG", "0") in {"1", "true", "yes", "y", "on"}:
                print(
                    "gemini_response",
                    {
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                        "body": response.text[:1000],
                    },
                )
            if response.status_code not in {429, 500, 502, 503, 504}:
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
        raise RuntimeError("Gemini response did not include output text.")
    return text
