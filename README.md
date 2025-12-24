# IOLApiClient

Cliente para consumir la API de InvertirOnline. Ya tiene:

- Caché de accesos administrada por `SQLiteAccessTokenRepo`, `SQLiteExtractionRepo` y un helper central (`src/seedwork/sqlite_db.py`) que comparte la misma base `seedwork.sqlite`.
- Servicio de autenticación estándar (`StandardAuthService`) emparejado con extractores que gestionan refresh/renew automaticos y token storage.
- `OptionMonitor` en el paquete `iol` que normaliza cotizaciones/options, calcula book, spread, moneyness y dispara alertas básicas.
- Helpers para generar requests (`iol/tickers`) y un cliente HTTP (`HttpxClientAdapter`) listos para nuevos endpoints.

## Cómo ejecutar

1. Configurar .env con `IOL_USERNAME` y `IOL_PASSWORD`, luego ejecutar el entrypoint:
   ```bash
   python3 -m main
   ```
2. La primera ejecución poblá `seedwork.sqlite` con tokens y logs de extracción.
3. Si querés explorar el monitor, fijate en `main.py` o instancia `OptionMonitor` desde otro módulo.
