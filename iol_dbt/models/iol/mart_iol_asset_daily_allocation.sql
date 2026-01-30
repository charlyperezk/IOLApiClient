{{ config(materialized='table') }}

with latest_snapshots as (
    select
        snapshot_id,
        fetched_at::date as report_date,
        fetched_at,
        row_number() over (
            partition by fetched_at::date
            order by fetched_at desc
        ) as rn
    from {{ ref('stg_iol_portfolio_raw') }}
    where status_code = 200
),
daily_latest as (
    select snapshot_id, report_date, fetched_at
    from latest_snapshots
    where rn = 1
),
assets as (
    select
        d.report_date,
        d.fetched_at as as_of,
        d.snapshot_id,
        f.symbol,
        f.daily_variation,
        f.value
    from daily_latest d
    join {{ ref('fct_iol_portfolio_assets') }} f
      on f.snapshot_id = d.snapshot_id
),
totals as (
    select
        report_date,
        coalesce(sum(value), 0) as total_value
    from assets
    group by report_date
)
select
    a.report_date,
    a.as_of,
    a.snapshot_id,
    a.symbol,
    a.daily_variation,
    a.value,
    t.total_value,
    case
        when t.total_value != 0 then (a.value / t.total_value) * 100.0
        else null
    end as participation_pct
from assets a
join totals t
  on t.report_date = a.report_date
