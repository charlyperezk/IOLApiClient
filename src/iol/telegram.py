import os
from typing import Optional

import httpx


def send_telegram_message(message: str, *, token: Optional[str] = None, chat_id: Optional[str] = None) -> None:
    token = token or os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = chat_id or os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    with httpx.Client(timeout=10) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()


def send_telegram_document(
    file_path: str | os.PathLike,
    *,
    caption: Optional[str] = None,
    token: Optional[str] = None,
    chat_id: Optional[str] = None,
) -> None:
    token = token or os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = chat_id or os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    data = {"chat_id": chat_id}
    if caption:
        data["caption"] = caption
    with httpx.Client(timeout=20) as client:
        with open(file_path, "rb") as file_handle:
            files = {"document": file_handle}
            response = client.post(url, data=data, files=files)
            response.raise_for_status()
