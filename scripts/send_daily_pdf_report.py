import asyncio
from datetime import date, datetime
from pathlib import Path
import sys
from typing import Any, Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

load_dotenv()

from src.seedwork.database import get_async_session_factory  # noqa: E402
from src.iol.gemini_summary import generate_daily_summary_text  # noqa: E402
from src.iol.telegram import send_telegram_document  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker  # noqa: E402
from weasyprint import HTML  # noqa: E402


async def fetch_daily_metrics(
    session_factory: async_sessionmaker[AsyncSession],
    report_date: Optional[date] = None,
) -> Optional[dict[str, Any]]:
    report_date = report_date or datetime.now().date()
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
        return {
            "report_date": row[0],
            "as_of": row[1],
            "total_value": float(row[2]) if row[2] is not None else 0.0,
            "delta_value": float(row[3]) if row[3] is not None else 0.0,
            "delta_pct": float(row[4]) if row[4] is not None else None,
            "top_gainers": row[5] or [],
            "top_losers": row[6] or [],
        }


async def fetch_distribution(
    session_factory: async_sessionmaker[AsyncSession],
    report_date: date,
    top_n: int = 8,
) -> list[tuple[str, float]]:
    sql = """
        with latest_snapshot as (
            select snapshot_id
            from iol.stg_iol_portfolio_raw
            where status_code = 200
              and fetched_at::date = :report_date
            order by fetched_at desc
            limit 1
        )
        select
            symbol,
            sum(value) as total_value
        from iol.fct_iol_portfolio_assets
        where snapshot_id = (select snapshot_id from latest_snapshot)
        group by symbol
        order by total_value desc
    """
    async with session_factory() as session:
        result = await session.execute(text(sql), {"report_date": report_date})
        rows = result.all()
        if not rows:
            return []

    rows = [(r[0], float(r[1])) for r in rows]
    if len(rows) <= top_n:
        return rows
    top = rows[:top_n]
    others_value = sum(v for _, v in rows[top_n:])
    top.append(("Otros", others_value))
    return top


def build_pie_chart(data: list[tuple[str, float]], output_path: Path) -> None:
    labels = [label for label, _ in data]
    values = [value for _, value in data]
    fig, ax = plt.subplots(figsize=(4.2, 3.2), dpi=150)
    ax.pie(
        values,
        labels=labels,
        autopct="%1.1f%%",
        startangle=140,
        textprops={"fontsize": 8},
    )
    ax.axis("equal")
    fig.tight_layout(pad=0.6)
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def render_html(
    *,
    report_date: date,
    total_value: float,
    delta_value: float,
    delta_pct: Optional[float],
    best_asset: Optional[str],
    best_var: Optional[float],
    best_participation: Optional[float],
    worst_asset: Optional[str],
    worst_var: Optional[float],
    worst_participation: Optional[float],
    narrative: str,
    pie_chart_path: Path,
) -> str:
    if delta_pct is None:
        day_status = "neutro"
    elif delta_pct > 0.1:
        day_status = "positivo"
    elif delta_pct < -0.1:
        day_status = "negativo"
    else:
        day_status = "neutro"

    bg_color = {
        "positivo": "#e8f5e9",
        "negativo": "#ffebee",
        "neutro": "#eeeeee",
    }[day_status]

    delta_pct_str = f"{delta_pct:+.2f}%" if delta_pct is not None else "n/a"
    best_var_str = f"{best_var:+.2f}%" if best_var is not None else "n/a"
    worst_var_str = f"{worst_var:+.2f}%" if worst_var is not None else "n/a"
    best_participation_str = (
        f"{best_participation:.2f}%" if best_participation is not None else "n/a"
    )
    worst_participation_str = (
        f"{worst_participation:.2f}%" if worst_participation is not None else "n/a"
    )

    return f"""
<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="utf-8" />
    <style>
      body {{
        font-family: Arial, sans-serif;
        background: {bg_color};
        padding: 24px;
        color: #1f1f1f;
      }}
      .card {{
        background: white;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
      }}
      h1 {{
        margin: 0 0 12px 0;
        font-size: 22px;
      }}
      .metrics {{
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 8px 16px;
        margin-top: 16px;
      }}
      .metric {{
        font-size: 14px;
      }}
      .narrative {{
        margin-top: 16px;
        font-size: 14px;
        line-height: 1.4;
      }}
      .chart {{
        margin-top: 20px;
        text-align: center;
      }}
      .chart img {{
        width: 360px;
        height: auto;
        display: inline-block;
      }}
      .footer {{
        margin-top: 20px;
        font-size: 12px;
        color: #666;
      }}
    </style>
  </head>
  <body>
    <div class="card">
      <h1>Reporte diario - {report_date.isoformat()}</h1>
      <div class="metrics">
        <div class="metric"><strong>Valor total:</strong> {total_value:,.2f}</div>
        <div class="metric"><strong>Variación diaria:</strong> {delta_value:+,.2f} ({delta_pct_str})</div>
        <div class="metric"><strong>Mejor activo:</strong> {best_asset or "n/a"} ({best_var_str}, {best_participation_str})</div>
        <div class="metric"><strong>Peor activo:</strong> {worst_asset or "n/a"} ({worst_var_str}, {worst_participation_str})</div>
      </div>
      <div class="narrative">{narrative}</div>
      <div class="chart">
        <img src="file://{pie_chart_path}" width="520" />
      </div>
      <div class="footer">Resumen generado automáticamente.</div>
    </div>
  </body>
</html>
"""


def parse_top_asset(
    items: list[dict[str, Any]], best: bool = True
) -> tuple[Optional[str], Optional[float], Optional[float]]:
    if not items:
        return None, None, None
    sorted_items = sorted(items, key=lambda x: x.get("daily_variation", 0.0), reverse=best)
    item = sorted_items[0]
    return item.get("symbol"), item.get("daily_variation"), item.get("participation_pct")


async def main() -> None:
    session_factory = get_async_session_factory()
    metrics = await fetch_daily_metrics(session_factory)
    if metrics is None:
        return
    report_date = metrics["report_date"]
    distribution = await fetch_distribution(session_factory, report_date)
    if not distribution:
        return

    pie_path = Path("/tmp/iol_portfolio_pie.png")
    build_pie_chart(distribution, pie_path)

    narrative = generate_daily_summary_text(metrics)
    best_symbol, best_var, best_participation = parse_top_asset(
        metrics["top_gainers"], best=True
    )
    worst_symbol, worst_var, worst_participation = parse_top_asset(
        metrics["top_losers"], best=False
    )

    html = render_html(
        report_date=report_date,
        total_value=metrics["total_value"],
        delta_value=metrics["delta_value"],
        delta_pct=metrics["delta_pct"],
        best_asset=best_symbol,
        best_var=best_var,
        best_participation=best_participation,
        worst_asset=worst_symbol,
        worst_var=worst_var,
        worst_participation=worst_participation,
        narrative=narrative,
        pie_chart_path=pie_path,
    )

    pdf_path = Path("/tmp/iol_daily_report.pdf")
    HTML(string=html).write_pdf(str(pdf_path))

    send_telegram_document(pdf_path, caption="Reporte diario de portafolio")


if __name__ == "__main__":
    asyncio.run(main())
