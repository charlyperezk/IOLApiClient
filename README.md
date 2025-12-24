# IOLApiClient

Cliente para consumir la API de InvertirOnline. Ya tiene:

- Caché de accesos administrada por `SQLiteAccessTokenRepo`, `SQLiteExtractionRepo` y un helper central (`src/seedwork/sqlite_db.py`) que comparte la misma base `db.sqlite`.
- Servicio de autenticación estándar (`StandardAuthService`) emparejado con extractores que gestionan refresh/renew automaticos y token storage.

## Cómo ejecutar

1. Configurar .env con `IOL_USERNAME` y `IOL_PASSWORD`:
2. La primera ejecución pobla `db.sqlite` con tokens.
3. La entidad extraction porta información de cada interacción con la API de iol, permite una robusta trazabilidad. Estas se irán almacenando en una tabla "extractions"
