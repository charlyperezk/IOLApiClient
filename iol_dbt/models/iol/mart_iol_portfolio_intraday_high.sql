{{ config(materialized='table') }}

with snapshot_totals as (
    select
        snapshot_id,
        fetched_at::date as report_date,
        fetched_at,
        coalesce(sum(value), 0) as total_value
    from {{ ref('fct_iol_portfolio_assets') }}
    group by snapshot_id, fetched_at
),
ranked as (
    select
        report_date,
        fetched_at,
        total_value,
        row_number() over (
            partition by report_date
            order by total_value desc, fetched_at desc
        ) as rn
    from snapshot_totals
)
select
    report_date,
    fetched_at as high_at,
    total_value as high_value
from ranked
where rn = 1
