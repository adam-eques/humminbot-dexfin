import asyncio
import json
import re
import sys
from ast import Constant
from datetime import datetime
from decimal import Decimal
from pprint import pprint
from typing import Any, Awaitable, NamedTuple, Optional
from unittest import TestCase
from unittest.mock import AsyncMock, patch
from warnings import catch_warnings

from aioresponses import aioresponses
from bidict import bidict
from numpy import record

import hummingbot.connector.exchange.dexfin.dexfin_utils as myutils
from hummingbot.connector.exchange.dexfin import dexfin_constants as CONSTANTS
from hummingbot.connector.exchange.dexfin import dexfin_web_utils as web_utils
from hummingbot.connector.exchange.dexfin.dexfin_api_order_book_data_source import DexfinAPIOrderBookDataSource
from hummingbot.connector.exchange.dexfin.dexfin_exchange import DexfinExchange
from hummingbot.connector.trading_rule import TradingRule
from hummingbot.connector.utils import get_new_client_order_id
from hummingbot.core.data_type.cancellation_result import CancellationResult
from hummingbot.core.data_type.common import OrderType, TradeType
from hummingbot.core.data_type.in_flight_order import InFlightOrder, OrderState
from hummingbot.core.data_type.trade_fee import TokenAmount
from hummingbot.core.event.event_logger import EventLogger
from hummingbot.core.event.events import (
    BuyOrderCompletedEvent,
    BuyOrderCreatedEvent,
    MarketEvent,
    MarketOrderFailureEvent,
    OrderCancelledEvent,
    OrderFilledEvent,
)
from hummingbot.core.network_iterator import NetworkStatus

# from pprint import pprint
# from decimal import Decimal
# import asyncio
# from typing import Any, Awaitable, NamedTuple, Optional

# from hummingbot.connector.exchange.dexfin.dexfin_exchange import DexfinExchange
# from hummingbot.connector.trading_rule import TradingRule
# from hummingbot.core.data_type.common import OrderType, TradeType
# from hummingbot.core.network_iterator import NetworkStatus


# def async_run_with_timeout(coroutine: Awaitable, timeout: float = 1):
#     ret = asyncio.get_event_loop().run_until_complete(asyncio.wait_for(coroutine, timeout))
#     return ret


# def main() -> int:
#     base_asset = "dxf"
#     quote_asset = "usdt"
#     trading_pair = f"{base_asset}-{quote_asset}"
#     exchange_trading_pair = f"{base_asset}{quote_asset}"
#     symbol = f"{base_asset}{quote_asset}"

#     exchange = DexfinExchange(
#         dexfin_api_key="4162b844db74efa5",
#         dexfin_secret_key="72c9f9307074287b82494dbd95e8a51e",
#         trading_pairs=[trading_pair]
#     )
#     exchange._dexfin_time_synchronizer.add_time_offset_ms_sample(0)
#     exchange._dexfin_time_synchronizer.logger().setLevel(1)
#     exchange._order_tracker.logger().setLevel(1)
#     exchange._trading_rules = {
#         trading_pair: TradingRule(
#             trading_pair=trading_pair,
#             min_order_size=Decimal(str(0.01)),
#             min_price_increment=Decimal(str(0.0001)),
#             min_base_amount_increment=Decimal(str(0.000001)),
#         )
#     }

#     status = async_run_with_timeout(exchange.check_network(), 1000)

#     connected = False
#     print("=============== Order Start ==============\n")
#     print("=============== Network Status ==============")
#     if NetworkStatus.CONNECTED == status:
#         print("Conencted")
#         status = async_run_with_timeout(
#             exchange._create_order(trade_type=TradeType.SELL,
#                                    order_id="OID1",
#                                    trading_pair=trading_pair,
#                                    amount=Decimal("0.15"),
#                                    order_type=OrderType.LIMIT,
#                                    price=Decimal("3")), 1000)
#         pprint(status)
#     else:
#         print("Not connected")


# if __name__ == '__main__':
#     # await main()
#     sys.exit(main())  # next section explains the use of sys.exit






class DexfinTest:
    # the level is required to receive logs from the data source logger
    level = 0

    def __init__(self):
        self.base_asset = "dxf"
        self.quote_asset = "usdt"
        self.trading_pair = f"{self.base_asset}-{self.quote_asset}"
        self.exchange_trading_pair = f"{self.base_asset}{self.quote_asset}"
        self.symbol = f"{self.base_asset}{self.quote_asset}"

        self.log_records = []
        self.test_task: Optional[asyncio.Task] = None

        api_key = "4162b844db74efa5"
        secret_key = "72c9f9307074287b82494dbd95e8a51e"
        self.exchange = DexfinExchange(
            dexfin_api_key=api_key,
            dexfin_secret_key=secret_key,
            trading_pairs=[self.trading_pair],
        )

        self.exchange.logger().setLevel(1)
        self.exchange.logger().addHandler(self)
        self.exchange._dexfin_time_synchronizer.add_time_offset_ms_sample(0)
        self.exchange._dexfin_time_synchronizer.logger().setLevel(1)
        self.exchange._dexfin_time_synchronizer.logger().addHandler(self)
        self.exchange._order_tracker.logger().setLevel(1)
        self.exchange._order_tracker.logger().addHandler(self)

        self._initialize_event_loggers()

        DexfinAPIOrderBookDataSource._trading_pair_symbol_map = {
            CONSTANTS.REST_URL: bidict(
                {f"{self.base_asset}{self.quote_asset}": self.trading_pair})
        }

        print("\n========== Prepare for order ==========\n")

        print(">> api_key: ", api_key)
        print(">> secret_key: ", secret_key)
        print(">> trading_pair: ", self.trading_pair)

    def _initialize_event_loggers(self):
        print("\n========== Initialize event loggers ==========\n")
        self.buy_order_completed_logger = EventLogger()
        self.buy_order_created_logger = EventLogger()
        self.order_cancelled_logger = EventLogger()
        self.order_failure_logger = EventLogger()
        self.order_filled_logger = EventLogger()
        self.sell_order_completed_logger = EventLogger()
        self.sell_order_created_logger = EventLogger()

        events_and_loggers = [
            (MarketEvent.BuyOrderCompleted, self.buy_order_completed_logger),
            (MarketEvent.BuyOrderCreated, self.buy_order_created_logger),
            (MarketEvent.OrderCancelled, self.order_cancelled_logger),
            (MarketEvent.OrderFailure, self.order_failure_logger),
            (MarketEvent.OrderFilled, self.order_filled_logger),
            (MarketEvent.SellOrderCompleted, self.sell_order_completed_logger),
            (MarketEvent.SellOrderCreated, self.sell_order_created_logger)]

        for event, logger in events_and_loggers:
            self.exchange.add_listener(event, logger)

    def handle(self, record):
        self.log_records.append(record)

    def _is_logged(self, log_level: str, message: str) -> bool:
        pprint(self.log_records)
        return any(record.levelname == log_level and record.getMessage() == message for record in self.log_records)

    def async_run_with_timeout(self, coroutine: Awaitable, timeout: float = 1):
        ret = asyncio.get_event_loop().run_until_complete(asyncio.wait_for(coroutine, timeout))
        return ret

    def _simulate_trading_rules_initialized(self):
        print("\n========== Simulate trading rules ==========\n")
        # print(">> Simulate trading rules\n")
        self.exchange._trading_rules = {
            self.trading_pair: TradingRule(
                trading_pair=self.trading_pair,
                min_order_size=Decimal(str(0.01)),
                min_price_increment=Decimal(str(0.0001)),
                min_base_amount_increment=Decimal(str(0.000001)),
            )
        }

    def _validate_auth_credentials_for_request(self, request_call_tuple: NamedTuple):
        self._validate_auth_credentials_taking_parameters_from_argument(
            request_call_tuple=request_call_tuple,
            params_key="params"
        )

    def _validate_auth_credentials_for_post_request(self, request_call_tuple: NamedTuple):
        self._validate_auth_credentials_taking_parameters_from_argument(
            request_call_tuple=request_call_tuple,
            params_key="data"
        )

    def get_order_state_mock(self, exchange_order_id: str = "someExchId") -> Any:
        order_state = {
            "id": exchange_order_id,
            "uuid": "fd01a864-ab92-11eb-8725-52739cef3139",
            "side": "sell",
            "ord_type": "limit",
            "price": "56632.793",
            "avg_price": "56632.793",
            "state": "done",
            "market": "btcusdt",
            "created_at": "2021-05-02T22:08:56Z",
            "updated_at": "2021-05-02T22:08:56Z",
            "origin_volume": "0.00019",
            "remaining_volume": "0.0",
            "executed_volume": "0.00019",
            "trades_count": 1,
            "trades": [
                {
                    "id": 1204442,
                    "price": "56632.793",
                    "amount": "0.00019",
                    "total": "10.76023067",
                    "market": "btcusdt",
                    "created_at": "2021-05-02T22:08:56Z",
                    "taker_type": "buy",
                    "side": "sell"
                }
            ]
        }
        return order_state

    def _validate_auth_credentials_taking_parameters_from_argument(self, request_call_tuple: NamedTuple,
                                                                   params_key: str):
        # request_params = request_call_tuple.kwargs[params_key]
        request_headers = request_call_tuple.kwargs["headers"]
        # self.assertIn("timestamp", request_params)
        pprint(request_headers)
        # self.assertIn("X-Auth-Apikey", request_headers)
        # self.assertIn("X-Auth-Nonce", request_headers)
        # self.assertEqual("testAPIKey", request_headers["X-Auth-Apikey"])

    def test_supported_order_types(self):
        supported_types = self.exchange.supported_order_types()
        print("\n========== Supported order types ==========\n")
        print(">> Supported order types", supported_types)

        # self.assertIn(OrderType.LIMIT, supported_types)
        # self.assertIn(OrderType.MARKET, supported_types)

    # @aioresponses()

    def test_check_network_successful(self):
        # url = web_utils.private_rest_url(CONSTANTS.PING_PATH_URL)
        # regex_url = re.compile(f"^{url}".replace(".", r"\.").replace("?", r"\?"))
        # mock_api.get(regex_url, body=json.dumps({}))
        pprint("========== Check network Status ==========")
        status = self.async_run_with_timeout(self.exchange.check_network(), 1000)
        if status == NetworkStatus.CONNECTED:
            pprint(">> Connected\n")
        else:
            pprint(">> Disconnected\n")
        # self.assertEqual(NetworkStatus.CONNECTED, status)

    def test_create_order_successfully(self):
        trade_type = TradeType.SELL
        order_id = "OID1"
        trading_pair = self.trading_pair
        amount = Decimal("0.09")
        order_type = OrderType.LIMIT
        price = Decimal("30")

        self._simulate_trading_rules_initialized()
        request_sent_event = asyncio.Event()
        url = web_utils.private_rest_url(CONSTANTS.ORDER_PATH_URL)
        status = self.async_run_with_timeout(
            self.exchange._create_order(trade_type=trade_type,
                                        order_id=order_id,
                                        trading_pair=trading_pair,
                                        amount=amount,
                                        order_type=order_type,
                                        price=price), 1000)

        print("\n========== Create order ==========\n")
        trade_type_str = ""
        if trade_type == TradeType.SELL:
            trade_type_str = "sell"
        else:
            trade_type_str = "buy"

        print(">> trade type: ", trade_type_str)
        print(">> order type: ", order_type)
        print(">> order id: ", order_id)
        print(">> trading pair: ", trading_pair)
        print(">> amount: ", amount)
        print(">> price: ", price)

        print("\n========== Order created successfully ==========\n")

    def last_order(self):
        print("\n========== Last created order ==========\n")
        status = self.async_run_with_timeout(
            self.exchange._get_last_order()
        )
        pprint(status)


def main() -> int:
    print("> Dexfin Connection Start")
    test = DexfinTest()

    test.test_create_order_successfully()
    test.last_order()
    print("\n> Dexfin Connection End")
    return 0


if __name__ == '__main__':
    # await main()
    sys.exit(main())  # next section explains the use of sys.exit
