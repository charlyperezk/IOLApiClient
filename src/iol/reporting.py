from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


_TZ = ZoneInfo("America/Argentina/Buenos_Aires")


@dataclass(frozen=True)
class DailyPortfolioSummary:
    as_of: datetime
    total_value: float
    delta_value: float
    delta_pct: Optional[float]
    top_gainers: list[tuple[str, float]]
    top_losers: list[tuple[str, float]]


async def _fetch_latest_snapshot_id(
    session: AsyncSession, target_date: date, identity: Optional[str]
) -> Optional[int]:
    sql = """
        select id
        from iol.iol_portfolio_raw_snapshots
        where status_code = 200
          and fetched_at::date = :target_date
          and (:identity is null or identity = :identity)
        order by fetched_at desc
        limit 1
    """
    result = await session.execute(
        text(sql), {"target_date": target_date, "identity": identity}
    )
    row = result.first()
    return int(row[0]) if row else None


async def _fetch_snapshot_stats(
    session: AsyncSession, snapshot_id: int, top_n: int
) -> tuple[datetime, float, list[tuple[str, float]], list[tuple[str, float]]]:
    total_sql = """
        select
            fetched_at,
            coalesce(sum((asset->>'valorizado')::numeric), 0) as total_value
        from iol.iol_portfolio_raw_snapshots s
        cross join lateral jsonb_array_elements(s.payload::jsonb->'activos') as asset
        where s.id = :snapshot_id
        group by fetched_at
    """
    total_result = await session.execute(text(total_sql), {"snapshot_id": snapshot_id})
    total_row = total_result.first()
    if not total_row:
        raise RuntimeError("Snapshot not found for stats")
    fetched_at = total_row[0]
    total_value = float(total_row[1])

    movers_sql = """
        select
            asset->'titulo'->>'simbolo' as symbol,
            (asset->>'variacionDiaria')::numeric as daily_variation
        from iol.iol_portfolio_raw_snapshots s
        cross join lateral jsonb_array_elements(s.payload::jsonb->'activos') as asset
        where s.id = :snapshot_id
        order by (asset->>'variacionDiaria')::numeric desc nulls last
        limit :top_n
    """
    gainers_result = await session.execute(
        text(movers_sql), {"snapshot_id": snapshot_id, "top_n": top_n}
    )
    top_gainers = [(row[0], float(row[1])) for row in gainers_result.all()]

    losers_sql = """
        select
            asset->'titulo'->>'simbolo' as symbol,
            (asset->>'variacionDiaria')::numeric as daily_variation
        from iol.iol_portfolio_raw_snapshots s
        cross join lateral jsonb_array_elements(s.payload::jsonb->'activos') as asset
        where s.id = :snapshot_id
        order by (asset->>'variacionDiaria')::numeric asc nulls last
        limit :top_n
    """
    losers_result = await session.execute(
        text(losers_sql), {"snapshot_id": snapshot_id, "top_n": top_n}
    )
    top_losers = [(row[0], float(row[1])) for row in losers_result.all()]

    return fetched_at, total_value, top_gainers, top_losers


async def build_daily_summary(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    identity: Optional[str] = None,
    target_date: Optional[date] = None,
    top_n: int = 3,
) -> Optional[DailyPortfolioSummary]:
    target_date = target_date or datetime.now(tz=_TZ).date()
    previous_date = target_date - timedelta(days=1)

    async with session_factory() as session:
        latest_id = await _fetch_latest_snapshot_id(session, target_date, identity)
        if latest_id is None:
            return None
        prev_id = await _fetch_latest_snapshot_id(session, previous_date, identity)

        fetched_at, total_value, top_gainers, top_losers = await _fetch_snapshot_stats(
            session, latest_id, top_n
        )

        delta_value = 0.0
        delta_pct = None
        if prev_id is not None:
            _, prev_total, _, _ = await _fetch_snapshot_stats(session, prev_id, top_n)
            delta_value = total_value - prev_total
            if prev_total:
                delta_pct = (delta_value / prev_total) * 100.0

    return DailyPortfolioSummary(
        as_of=fetched_at,
        total_value=total_value,
        delta_value=delta_value,
        delta_pct=delta_pct,
        top_gainers=top_gainers,
        top_losers=top_losers,
    )


def format_daily_summary(summary: DailyPortfolioSummary) -> str:
    delta_pct_str = (
        f"{summary.delta_pct:+.2f}%"
        if summary.delta_pct is not None
        else "n/a"
    )
    lines = [
        f"Resumen diario (IOL) - {summary.as_of:%Y-%m-%d %H:%M}",
        f"Total: {summary.total_value:,.2f}",
        f"Delta dia: {summary.delta_value:+,.2f} ({delta_pct_str})",
        "",
        "Top ganadores:",
    ]
    for symbol, var in summary.top_gainers:
        lines.append(f"- {symbol}: {var:+.2f}%")
    lines.append("")
    lines.append("Top perdedores:")
    for symbol, var in summary.top_losers:
        lines.append(f"- {symbol}: {var:+.2f}%")
    return "\n".join(lines)
