{{ config(materialized='table') }}

with latest_snapshots as (
    select
        snapshot_id,
        fetched_at,
        fetched_at::date as report_date,
        row_number() over (
            partition by fetched_at::date
            order by fetched_at desc
        ) as rn
    from {{ ref('stg_iol_portfolio_raw') }}
    where status_code = 200
),
daily_latest as (
    select snapshot_id, fetched_at, report_date
    from latest_snapshots
    where rn = 1
),
assets as (
    select
        d.report_date,
        d.fetched_at as as_of,
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
        max(as_of) as as_of,
        coalesce(sum(value), 0) as total_value
    from assets
    group by report_date
),
prev_totals as (
    select
        report_date,
        total_value as prev_total
    from totals
),
daily_moves as (
    select
        a.report_date,
        a.symbol,
        a.daily_variation,
        case
            when t.total_value is not null and t.total_value != 0
                then (a.value / t.total_value) * 100.0
            else null
        end as participation_pct,
        row_number() over (
            partition by a.report_date
            order by daily_variation desc nulls last
        ) as rn_gainers,
        row_number() over (
            partition by a.report_date
            order by daily_variation asc nulls last
        ) as rn_losers
    from assets a
    join totals t
      on t.report_date = a.report_date
),
gainers as (
    select
        report_date,
        jsonb_agg(
            jsonb_build_object(
                'symbol', symbol,
                'daily_variation', daily_variation,
                'participation_pct', participation_pct
            )
            order by daily_variation desc nulls last
        ) as top_gainers
    from daily_moves
    where rn_gainers <= 3
    group by report_date
),
losers as (
    select
        report_date,
        jsonb_agg(
            jsonb_build_object(
                'symbol', symbol,
                'daily_variation', daily_variation,
                'participation_pct', participation_pct
            )
            order by daily_variation asc nulls last
        ) as top_losers
    from daily_moves
    where rn_losers <= 3
    group by report_date
)
select
    t.report_date,
    t.as_of,
    t.total_value,
    (t.total_value - p.prev_total) as delta_value,
    case
        when p.prev_total is not null and p.prev_total != 0
            then ((t.total_value - p.prev_total) / p.prev_total) * 100.0
        else null
    end as delta_pct,
    g.top_gainers,
    l.top_losers
from totals t
left join prev_totals p
    on p.report_date = t.report_date - interval '1 day'
left join gainers g
    on g.report_date = t.report_date
left join losers l
    on l.report_date = t.report_date
