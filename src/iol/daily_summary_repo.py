from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional
import json
from zoneinfo import ZoneInfo

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


_TZ = ZoneInfo("America/Argentina/Buenos_Aires")


async def fetch_daily_summary(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    report_date: Optional[date] = None,
) -> Optional[dict[str, Any]]:
    report_date = report_date or datetime.now(_TZ).date()
    sql = """
        select
            report_date,
            as_of,
            total_value,
            delta_value,
            delta_pct,
            top_gainers,
            top_losers
        from iol.mart_iol_portfolio_daily
        where report_date = :report_date
        limit 1
    """
    async with session_factory() as session:
        result = await session.execute(text(sql), {"report_date": report_date})
        row = result.first()
        if not row:
            return None
        def _parse_json(value: Any) -> Any:
            if value is None:
                return []
            if isinstance(value, (list, dict)):
                return value
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return []
            return []

        return {
            "report_date": row[0],
            "as_of": row[1],
            "total_value": float(row[2]) if row[2] is not None else 0.0,
            "delta_value": float(row[3]) if row[3] is not None else 0.0,
            "delta_pct": float(row[4]) if row[4] is not None else None,
            "top_gainers": _parse_json(row[5]),
            "top_losers": _parse_json(row[6]),
        }
