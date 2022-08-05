from cgitb import enable
from datetime import datetime
from decimal import Decimal
from pprint import pprint
from typing import Any, Dict

from hummingbot.client.config.config_methods import using_exchange
from hummingbot.client.config.config_var import ConfigVar
from hummingbot.core.data_type.trade_fee import TradeFeeSchema

CENTRALIZED = True
EXAMPLE_PAIR = "ZRX-ETH"

DEFAULT_FEES = TradeFeeSchema(
    maker_percent_fee_decimal=Decimal("0.001"),
    taker_percent_fee_decimal=Decimal("0.001"),
    buy_percent_fee_deducted_from_returns=True
)


def is_exchange_information_valid(exchange_info: Dict[str, Any]) -> bool:
    """
    Verifies if a trading pair is enabled to operate with based on its exchange information
    :param exchange_info: the exchange information for a trading pair
    :return: True if the trading pair is enabled, False otherwise
    """
    # return exchange_info.get("status", None) == "TRADING" and "SPOT" in exchange_info.get("permissions", list())
    return exchange_info.get("state", None) == "enabled"


def iso_datetime_to_timestamp(date_time: str) -> int:
    new_datetime = date_time
    if new_datetime.endswith("Z"):
        new_datetime = new_datetime.replace("Z", "+00:00")
    return int(datetime.fromisoformat(new_datetime).timestamp() * 1e3)


KEYS = {
    "dexfin_api_key":
        ConfigVar(key="dexfin_api_key",
                  prompt="Enter your Dexfin API key >>> ",
                  required_if=using_exchange("dexfin"),
                  is_secure=True,
                  is_connect_key=True),
    "dexfin_secret_key":
        ConfigVar(key="dexfin_secret_key",
                  prompt="Enter your Dexfin API secret >>> ",
                  required_if=using_exchange("dexfin"),
                  is_secure=True,
                  is_connect_key=True),
}

# OTHER_DOMAINS = ["binance_us"]
# OTHER_DOMAINS_PARAMETER = {"binance_us": "us"}
# OTHER_DOMAINS_EXAMPLE_PAIR = {"binance_us": "BTC-USDT"}
# OTHER_DOMAINS_DEFAULT_FEES = {"binance_us": [0.1, 0.1]}
# OTHER_DOMAINS_KEYS = {"binance_us": {
#     "binance_us_api_key":
#         ConfigVar(key="binance_us_api_key",
#                   prompt="Enter your Binance US API key >>> ",
#                   required_if=using_exchange("binance_us"),
#                   is_secure=True,
#                   is_connect_key=True),
#     "binance_us_api_secret":
#         ConfigVar(key="binance_us_api_secret",
#                   prompt="Enter your Binance US API secret >>> ",
#                   required_if=using_exchange("binance_us"),
#                   is_secure=True,
#                   is_connect_key=True),
# }}
