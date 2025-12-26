ACCESS_TOKEN_DEFAULT_LIFETIME = 300
HOST = "https://api.invertironline.com"
API_ROOT_V2 = HOST + "/api/v2"

TOKEN_PATH = HOST + "/token"
ME_PATH = API_ROOT_V2 + "/datos-perfil"
PORTFOLIO_PATH = API_ROOT_V2 + "/portafolio/{country}"
TICKER_COTIZATION_PATH = API_ROOT_V2 + "/{market}/Titulos/{symbol}/CotizacionDetalle"
ALL_COTIZATIONS_PATH = API_ROOT_V2 + "/Cotizaciones/{symbol}/{country}/Todos"