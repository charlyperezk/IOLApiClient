{{ config(materialized='table') }}

with latest_snapshot as (
    select snapshot_id, fetched_at
    from {{ ref('stg_iol_portfolio_raw') }}
    where status_code = 200
    order by fetched_at desc
    limit 1
),
current_values as (
    select
        f.symbol,
        f.value as current_value,
        f.fetched_at as current_at
    from {{ ref('fct_iol_portfolio_assets') }} f
    where f.snapshot_id = (select snapshot_id from latest_snapshot)
),
ranked_highs as (
    select
        f.symbol,
        f.value as high_value,
        f.fetched_at as high_at,
        row_number() over (
            partition by f.symbol
            order by f.value desc nulls last, f.fetched_at desc
        ) as rn
    from {{ ref('fct_iol_portfolio_assets') }} f
),
highs as (
    select symbol, high_value, high_at
    from ranked_highs
    where rn = 1
)
select
    h.symbol,
    h.high_at,
    h.high_value,
    c.current_at,
    c.current_value
from highs h
left join current_values c
    on c.symbol = h.symbol
