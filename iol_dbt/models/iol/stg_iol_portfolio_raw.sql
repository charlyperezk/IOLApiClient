{{ config(materialized='view') }}

select
    id as snapshot_id,
    identity,
    country,
    status_code,
    fetched_at,
    created_at,
    payload
from {{ source('iol', 'iol_portfolio_raw_snapshots') }}
