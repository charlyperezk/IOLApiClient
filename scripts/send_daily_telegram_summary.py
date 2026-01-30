import asyncio
from pathlib import Path
import sys

from dotenv import load_dotenv

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

load_dotenv()

from src.seedwork.database import get_async_session_factory  # noqa: E402
from src.iol.daily_summary_repo import fetch_daily_summary  # noqa: E402
from src.iol.gemini_summary import generate_daily_summary_text  # noqa: E402
from src.iol.telegram import send_telegram_message  # noqa: E402


async def main() -> None:
    session_factory = get_async_session_factory()
    metrics = await fetch_daily_summary(session_factory)
    if metrics is None:
        send_telegram_message("No hay snapshots para generar el resumen de hoy.")
        return
    message = generate_daily_summary_text(metrics)
    send_telegram_message(message)


if __name__ == "__main__":
    asyncio.run(main())
