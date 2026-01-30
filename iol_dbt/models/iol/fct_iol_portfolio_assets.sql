{{ config(materialized='table') }}

with snapshots as (
    select *
    from {{ ref('stg_iol_portfolio_raw') }}
    where status_code = 200
),
assets as (
    select
        s.snapshot_id,
        s.identity,
        s.country,
        s.fetched_at,
        s.created_at,
        asset as raw_asset
    from snapshots s
    cross join lateral jsonb_array_elements(s.payload::jsonb->'activos') as asset
)
select
    snapshot_id,
    identity,
    country,
    fetched_at,
    created_at,
    raw_asset->'titulo'->>'simbolo' as symbol,
    raw_asset->'titulo'->>'descripcion' as description,
    raw_asset->'titulo'->>'pais' as title_country,
    raw_asset->'titulo'->>'mercado' as market,
    raw_asset->'titulo'->>'tipo' as asset_type,
    raw_asset->'titulo'->>'plazo' as term,
    raw_asset->'titulo'->>'moneda' as currency,
    (raw_asset->>'cantidad')::numeric as quantity,
    (raw_asset->>'comprometido')::numeric as committed,
    (raw_asset->>'puntosVariacion')::numeric as points_variation,
    (raw_asset->>'variacionDiaria')::numeric as daily_variation,
    (raw_asset->>'ultimoPrecio')::numeric as last_price,
    (raw_asset->>'ppc')::numeric as average_cost,
    (raw_asset->>'gananciaPorcentaje')::numeric as profit_pct,
    (raw_asset->>'gananciaDinero')::numeric as profit_amount,
    (raw_asset->>'valorizado')::numeric as value,
    raw_asset->'parking' as parking,
    raw_asset as raw_payload
from assets
