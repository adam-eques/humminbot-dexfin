from hummingbot.core.api_throttler.data_types import LinkedLimitWeightPair, RateLimit
from hummingbot.core.data_type.in_flight_order import OrderState

DEFAULT_DOMAIN = "com"

HBOT_ORDER_ID_PREFIX = "x-XEKWYICX"
MAX_ORDER_ID_LEN = 36

# Base URL
REST_URL = "https://trade.dexfin.com/api/v2/peatio"
WSS_URL = ""

# PUBLIC_API_VERSION = "v2"
# PRIVATE_API_VERSION = "v2"

# Public API endpoints or BinanceClient function
TICKER_PRICE_CHANGE_PATH_URL = "/public/markets/tickers"
EXCHANGE_INFO_PATH_URL = "/public/markets"
PING_PATH_URL = "/public/health/alive"
SNAPSHOT_PATH_URL = "/public/markets/{}/depth"
SERVER_TIME_PATH_URL = "/public/timestamp"

# Private API endpoints or BinanceClient function
ACCOUNTS_PATH_URL = "/account/balances"
MY_TRADES_PATH_URL = "/market/trades"
ORDER_PATH_URL = "/market/orders"
ORDER_CANCEL_URL = "/market/orders/{}/cancel"
BINANCE_USER_STREAM_PATH_URL = "/userDataStream"
ORDER_INFO_URL = "/market/orders/{}"

WS_HEARTBEAT_TIME_INTERVAL = 30

# Binance params

SIDE_BUY = 'BUY'
SIDE_SELL = 'SELL'

TIME_IN_FORCE_GTC = 'GTC'  # Good till cancelled
TIME_IN_FORCE_IOC = 'IOC'  # Immediate or cancel
TIME_IN_FORCE_FOK = 'FOK'  # Fill or kill

# Rate Limit Type
REQUEST_WEIGHT = "REQUEST_WEIGHT"
ORDERS = "ORDERS"
ORDERS_24HR = "ORDERS_24HR"

# Rate Limit time intervals
ONE_MINUTE = 60
ONE_SECOND = 1
ONE_DAY = 86400

MAX_REQUEST = 5000

# Order States
# ORDER_STATE = {
#     "PENDING": OrderState.PENDING_CREATE,
#     "NEW": OrderState.OPEN,
#     "FILLED": OrderState.FILLED,
#     "PARTIALLY_FILLED": OrderState.PARTIALLY_FILLED,
#     "PENDING_CANCEL": OrderState.OPEN,
#     "CANCELED": OrderState.CANCELED,
#     "REJECTED": OrderState.FAILED,
#     "EXPIRED": OrderState.FAILED,
# }
ORDER_STATE = {
    "wait": OrderState.PENDING_CREATE,
    # "NEW": OrderState.OPEN,
    "done": OrderState.FILLED,
    # "PARTIALLY_FILLED": OrderState.PARTIALLY_FILLED,
    # "PENDING_CANCEL": OrderState.OPEN,
    "cancel": OrderState.CANCELED,
    # "REJECTED": OrderState.FAILED,
    # "EXPIRED": OrderState.FAILED,
}

# Websocket event types
DIFF_EVENT_TYPE = "depthUpdate"
TRADE_EVENT_TYPE = "trade"

RATE_LIMITS = [
    # Pools
    RateLimit(limit_id=REQUEST_WEIGHT, limit=1200, time_interval=ONE_MINUTE),
    RateLimit(limit_id=ORDERS, limit=10, time_interval=ONE_SECOND),
    RateLimit(limit_id=ORDERS_24HR, limit=100000, time_interval=ONE_DAY),
    # Weighted Limits
    RateLimit(limit_id=TICKER_PRICE_CHANGE_PATH_URL, limit=MAX_REQUEST, time_interval=ONE_MINUTE,
              linked_limits=[LinkedLimitWeightPair(REQUEST_WEIGHT, 40)]),
    RateLimit(limit_id=EXCHANGE_INFO_PATH_URL, limit=MAX_REQUEST, time_interval=ONE_MINUTE,
              linked_limits=[(LinkedLimitWeightPair(REQUEST_WEIGHT, 10))]),
    RateLimit(limit_id=SNAPSHOT_PATH_URL, limit=MAX_REQUEST, time_interval=ONE_MINUTE,
              linked_limits=[LinkedLimitWeightPair(REQUEST_WEIGHT, 50)]),
    RateLimit(limit_id=BINANCE_USER_STREAM_PATH_URL, limit=MAX_REQUEST, time_interval=ONE_MINUTE,
              linked_limits=[LinkedLimitWeightPair(REQUEST_WEIGHT, 1)]),
    RateLimit(limit_id=SERVER_TIME_PATH_URL, limit=MAX_REQUEST, time_interval=ONE_MINUTE,
              linked_limits=[LinkedLimitWeightPair(REQUEST_WEIGHT, 1)]),
    RateLimit(limit_id=PING_PATH_URL, limit=MAX_REQUEST, time_interval=ONE_MINUTE,
              linked_limits=[LinkedLimitWeightPair(REQUEST_WEIGHT, 1)]),
    RateLimit(limit_id=ACCOUNTS_PATH_URL, limit=MAX_REQUEST, time_interval=ONE_MINUTE,
              linked_limits=[LinkedLimitWeightPair(REQUEST_WEIGHT, 10)]),
    RateLimit(limit_id=MY_TRADES_PATH_URL, limit=MAX_REQUEST, time_interval=ONE_MINUTE,
              linked_limits=[LinkedLimitWeightPair(REQUEST_WEIGHT, 10)]),
    RateLimit(limit_id=ORDER_PATH_URL, limit=MAX_REQUEST, time_interval=ONE_MINUTE,
              linked_limits=[LinkedLimitWeightPair(REQUEST_WEIGHT, 1),
                             LinkedLimitWeightPair(ORDERS, 1),
                             LinkedLimitWeightPair(ORDERS_24HR, 1)]),
]
