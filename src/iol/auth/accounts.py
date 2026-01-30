import os
from typing import Callable, Optional, Tuple


ACCOUNTS: dict[str, Callable[[], Optional[str]]] = {
    "TEST": lambda: os.getenv("IOL_USERNAME"),
}

PASSWORDS: dict[str, Callable[[], Optional[str]]] = {
    "TEST": lambda: os.getenv("IOL_PASSWORD"),
}


def get_credentials(identifier: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    if not identifier:
        identifier = os.getenv("DEFAULT_IDENTITY")
    if not identifier:
        return None, None
    username_provider = ACCOUNTS.get(identifier)
    password_provider = PASSWORDS.get(identifier)
    username = username_provider() if username_provider else None
    password = password_provider() if password_provider else None
    return username, password
