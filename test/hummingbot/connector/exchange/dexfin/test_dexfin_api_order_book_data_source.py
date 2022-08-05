import asyncio
import json
import re
import unittest
from array import ArrayType
from decimal import Decimal
from pprint import pprint
from test.hummingbot.connector.network_mocking_assistant import NetworkMockingAssistant
from typing import Any, Awaitable, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

from aioresponses.core import aioresponses
from bidict import bidict

import hummingbot.connector.exchange.dexfin.dexfin_constants as CONSTANTS
import hummingbot.connector.exchange.dexfin.dexfin_web_utils as web_utils
from hummingbot.connector.exchange.dexfin.dexfin_api_order_book_data_source import DexfinAPIOrderBookDataSource
from hummingbot.connector.time_synchronizer import TimeSynchronizer
from hummingbot.core.api_throttler.async_throttler import AsyncThrottler
from hummingbot.core.data_type.order_book import OrderBook
from hummingbot.core.data_type.order_book_message import OrderBookMessage


class DexfinAPIOrderBookDataSourceUnitTests(unittest.TestCase):
    # logging.Level required to receive logs from the data source logger
    level = 0

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.ev_loop = asyncio.get_event_loop()
        cls.base_asset = "btc"
        cls.quote_asset = "usdt"
        # cls.trading_pair = f"{cls.base_asset}-{cls.quote_asset}"
        cls.trading_pair = cls.base_asset + cls.quote_asset
        cls.ex_trading_pair = cls.base_asset + cls.quote_asset
        cls.base_url = CONSTANTS.REST_URL
        for task in asyncio.all_tasks(loop=cls.ev_loop):
            task.cancel()

    @classmethod
    def tearDownClass(cls) -> None:
        for task in asyncio.all_tasks(loop=cls.ev_loop):
            task.cancel()

    def setUp(self) -> None:
        super().setUp()
        self.log_records = []
        self.listening_task = None
        self.mocking_assistant = NetworkMockingAssistant()
        self.time_synchronizer = TimeSynchronizer()
        self.time_synchronizer.add_time_offset_ms_sample(1000)

        self.throttler = AsyncThrottler(rate_limits=CONSTANTS.RATE_LIMITS)
        self.data_source = DexfinAPIOrderBookDataSource(trading_pairs=[self.trading_pair],
                                                        throttler=self.throttler,
                                                        base_url=self.base_url,
                                                        time_synchronizer=self.time_synchronizer)
        self.data_source.logger().setLevel(1)
        self.data_source.logger().addHandler(self)

        self.resume_test_event = asyncio.Event()

        DexfinAPIOrderBookDataSource._trading_pair_symbol_map = {
            CONSTANTS.REST_URL: bidict(
                {f"{self.base_asset}{self.quote_asset}": self.trading_pair})
        }

    def tearDown(self) -> None:
        self.listening_task and self.listening_task.cancel()
        DexfinAPIOrderBookDataSource._trading_pair_symbol_map = {}
        super().tearDown()

    def handle(self, record):
        self.log_records.append(record)

    def _is_logged(self, log_level: str, message: str) -> bool:
        return any(record.levelname == log_level and record.getMessage() == message
                   for record in self.log_records)

    def _create_exception_and_unlock_test_with_event(self, exception):
        self.resume_test_event.set()
        raise exception

    def async_run_with_timeout(self, coroutine: Awaitable, timeout: float = 1):
        ret = self.ev_loop.run_until_complete(asyncio.wait_for(coroutine, timeout))
        return ret

    def _successfully_subscribed_event(self):
        resp = {
            "result": None,
            "id": 1
        }
        return resp

    def _trade_update_event(self):
        resp = {
            "e": "trade",
            "E": 123456789,
            "s": self.ex_trading_pair,
            "t": 12345,
            "p": "0.001",
            "q": "100",
            "b": 88,
            "a": 50,
            "T": 123456785,
            "m": True,
            "M": True
        }
        return resp

    def _order_diff_event(self):
        resp = {
            "e": "depthUpdate",
            "E": 123456789,
            "s": self.ex_trading_pair,
            "U": 157,
            "u": 160,
            "b": [["0.0024", "10"]],
            "a": [["0.0026", "100"]]
        }
        return resp

    def _snapshot_response(self):
        resp = {
            "timestamp": 1656483612,
            "asks": [
                [
                    "20129.014",
                    "0.006"
                ],
                [
                    "20222.814",
                    "0.005"
                ],
                [
                    "20274.48",
                    "0.006"
                ],
                [
                    "20307.685",
                    "0.002"
                ],
                [
                    "20333.73",
                    "0.028"
                ],
                [
                    "20342.177",
                    "0.003"
                ],
                [
                    "20352.82",
                    "0.003"
                ],
                [
                    "20399.504",
                    "0.001"
                ],
                [
                    "20431.679",
                    "0.067"
                ],
                [
                    "20440.113",
                    "0.065"
                ],
                [
                    "20453.524",
                    "0.003"
                ],
                [
                    "20457.174",
                    "0.002"
                ],
                [
                    "20463.023",
                    "0.004"
                ],
                [
                    "20474.434",
                    "0.007"
                ],
                [
                    "20503.698",
                    "0.007"
                ],
                [
                    "20687.854",
                    "0.006"
                ],
                [
                    "20775.848",
                    "0.06"
                ],
                [
                    "24446.353",
                    "0.006"
                ],
                [
                    "30479.956",
                    "0.008"
                ],
                [
                    "32411.024",
                    "0.008"
                ],
                [
                    "32498.296",
                    "0.002"
                ],
                [
                    "34767.933",
                    "0.004"
                ],
                [
                    "34900.524",
                    "0.009"
                ],
                [
                    "34959.79",
                    "0.003"
                ],
                [
                    "35079.892",
                    "0.004"
                ],
                [
                    "35109.484",
                    "0.009"
                ],
                [
                    "35191.272",
                    "0.005"
                ],
                [
                    "35208.465",
                    "0.007"
                ],
                [
                    "49146.97",
                    "0.003"
                ],
                [
                    "49441.374",
                    "0.01"
                ],
                [
                    "49731.078",
                    "0.015"
                ],
                [
                    "51434.844",
                    "0.005"
                ],
                [
                    "51466.588",
                    "0.005"
                ],
                [
                    "51525.177",
                    "0.014"
                ],
                [
                    "51618.948",
                    "0.015"
                ],
                [
                    "51986.193",
                    "0.003"
                ],
                [
                    "52311.46",
                    "0.004"
                ],
                [
                    "55047.98",
                    "0.017"
                ],
                [
                    "60000.0",
                    "0.00082"
                ]
            ],
            "bids": [
                [
                    "20015.365",
                    "0.006"
                ],
                [
                    "20008.263",
                    "0.002"
                ],
                [
                    "19940.587",
                    "0.009"
                ],
                [
                    "19916.673",
                    "0.003"
                ],
                [
                    "19890.501",
                    "0.008"
                ],
                [
                    "19852.159",
                    "0.009"
                ],
                [
                    "19817.817",
                    "0.003"
                ],
                [
                    "19777.547",
                    "0.039"
                ],
                [
                    "19773.297",
                    "0.014"
                ],
                [
                    "19765.907",
                    "0.007"
                ],
                [
                    "19755.841",
                    "0.003"
                ],
                [
                    "19704.471",
                    "0.009"
                ],
                [
                    "19689.538",
                    "0.042"
                ],
                [
                    "14471.544",
                    "0.009"
                ],
                [
                    "13194.614",
                    "0.009"
                ],
                [
                    "13027.237",
                    "0.01"
                ],
                [
                    "10641.9",
                    "0.008"
                ],
                [
                    "9395.542",
                    "0.012"
                ],
                [
                    "5052.092",
                    "0.009"
                ],
                [
                    "100.0",
                    "0.001"
                ],
                [
                    "0.011",
                    "8567.438"
                ]
            ]
        }
        return resp

    @aioresponses()
    def test_get_last_trade_prices(self, mock_api):
        url = web_utils.public_rest_url(path_url=CONSTANTS.TICKER_PRICE_CHANGE_PATH_URL, base_url=self.base_url)
        url = f"{url}?symbol={self.base_asset}{self.quote_asset}"
        regex_url = re.compile(f"^{url}".replace(".", r"\.").replace("?", r"\?"))

        mock_response = {
            "symbol": "BNBBTC",
            "priceChange": "-94.99999800",
            "priceChangePercent": "-95.960",
            "weightedAvgPrice": "0.29628482",
            "prevClosePrice": "0.10002000",
            "lastPrice": "100.0",
            "lastQty": "200.00000000",
            "bidPrice": "4.00000000",
            "bidQty": "100.00000000",
            "askPrice": "4.00000200",
            "askQty": "100.00000000",
            "openPrice": "99.00000000",
            "highPrice": "100.00000000",
            "lowPrice": "0.10000000",
            "volume": "8913.30000000",
            "quoteVolume": "15.30000000",
            "openTime": 1499783499040,
            "closeTime": 1499869899040,
            "firstId": 28385,
            "lastId": 28460,
            "count": 76,
        }

        mock_api.get(regex_url, body=json.dumps(mock_response))

        result: Dict[str, float] = self.async_run_with_timeout(
            self.data_source.get_last_traded_prices(trading_pairs=[self.trading_pair],
                                                    throttler=self.throttler,
                                                    time_synchronizer=self.time_synchronizer)
        )

        self.assertEqual(1, len(result))
        self.assertEqual(100, result[self.trading_pair])

    @aioresponses()
    def test_get_all_mid_prices(self, mock_api):
        url = web_utils.public_rest_url(path_url=CONSTANTS.TICKER_PRICE_CHANGE_PATH_URL, base_url=self.base_url)

        mock_response: List[Dict[str, Any]] = {
            "btcusdt": {
                "at": "1656581401",
                "ticker": {
                    "low": "18968.762",
                    "high": "20419.99",
                    "open": "20182.62",
                    "last": "18968.762",
                    "volume": "6048141.02015701",
                    "amount": "302.450999999996",
                    "avg_price": "19997",
                    "price_change_percent": "-6.01%",
                    "vol": "6048141.02015701"
                }
            },
            "btceur": {
                "at": "1656581401",
                "ticker": {
                    "low": "18184.199",
                    "high": "19533.011",
                    "open": "19171.171",
                    "last": "18185.63",
                    "volume": "4604152.76236901",
                    "amount": "241.093999999999",
                    "avg_price": "19096.919717492",
                    "price_change_percent": "-5.14%",
                    "vol": "4604152.76236901"
                }
            },
            "btcczk": {
                "at": "1656581401",
                "ticker": {
                    "low": "419468.14",
                    "high": "451574.01",
                    "open": "446557.74",
                    "last": "419744.46",
                    "volume": "103717554.391931",
                    "amount": "234.414499999999",
                    "avg_price": "442453.663881419",
                    "price_change_percent": "-6.00%",
                    "vol": "103717554.391931"
                }
            },
            "dxfczk": {
                "at": "1656581401",
                "ticker": {
                    "low": "0.0",
                    "high": "0.0",
                    "open": "0.0",
                    "last": "0.562",
                    "volume": "0.0",
                    "amount": "0.0",
                    "avg_price": "0.0",
                    "price_change_percent": "+0.00%",
                    "vol": "0.0"
                }
            },
            "dxfusdt": {
                "at": "1656581401",
                "ticker": {
                    "low": "0.01828",
                    "high": "0.01915",
                    "open": "0.01913",
                    "last": "0.01828",
                    "volume": "146082.6908302",
                    "amount": "7777611.80900002",
                    "avg_price": "0.0187824610455818",
                    "price_change_percent": "-4.44%",
                    "vol": "146082.6908302"
                }
            },
            "vrczk": {
                "at": "1656581401",
                "ticker": {
                    "low": "0.0",
                    "high": "0.0",
                    "open": "0.0",
                    "last": "1.18",
                    "volume": "0.0",
                    "amount": "0.0",
                    "avg_price": "0.0",
                    "price_change_percent": "+0.00%",
                    "vol": "0.0"
                }
            }
        }

        mock_api.get(url, body=json.dumps(mock_response))

        result: Dict[str, float] = self.async_run_with_timeout(
            self.data_source.get_all_mid_prices()
        )

        pprint(result)
        self.assertEqual(1, len(result))
        self.assertEqual(Decimal(19997), result[self.trading_pair])

    @aioresponses()
    def test_fetch_trading_pairs(self, mock_api):
        DexfinAPIOrderBookDataSource._trading_pair_symbol_map = {}
        url = web_utils.public_rest_url(path_url=CONSTANTS.EXCHANGE_INFO_PATH_URL, base_url=self.base_url)

        # mock_response: Dict[str, Any] = {
        #     "timezone": "UTC",
        #     "serverTime": 1639598493658,
        #     "rateLimits": [],
        #     "exchangeFilters": [],
        #     "symbols": [
        #         {
        #             "symbol": "ETHBTC",
        #             "status": "TRADING",
        #             "baseAsset": "ETH",
        #             "baseAssetPrecision": 8,
        #             "quoteAsset": "BTC",
        #             "quotePrecision": 8,
        #             "quoteAssetPrecision": 8,
        #             "baseCommissionPrecision": 8,
        #             "quoteCommissionPrecision": 8,
        #             "orderTypes": [
        #                 "LIMIT",
        #                 "LIMIT_MAKER",
        #                 "MARKET",
        #                 "STOP_LOSS_LIMIT",
        #                 "TAKE_PROFIT_LIMIT"
        #             ],
        #             "icebergAllowed": True,
        #             "ocoAllowed": True,
        #             "quoteOrderQtyMarketAllowed": True,
        #             "isSpotTradingAllowed": True,
        #             "isMarginTradingAllowed": True,
        #             "filters": [],
        #             "permissions": [
        #                 "SPOT",
        #                 "MARGIN"
        #             ]
        #         },
        #         {
        #             "symbol": "LTCBTC",
        #             "status": "TRADING",
        #             "baseAsset": "LTC",
        #             "baseAssetPrecision": 8,
        #             "quoteAsset": "BTC",
        #             "quotePrecision": 8,
        #             "quoteAssetPrecision": 8,
        #             "baseCommissionPrecision": 8,
        #             "quoteCommissionPrecision": 8,
        #             "orderTypes": [
        #                 "LIMIT",
        #                 "LIMIT_MAKER",
        #                 "MARKET",
        #                 "STOP_LOSS_LIMIT",
        #                 "TAKE_PROFIT_LIMIT"
        #             ],
        #             "icebergAllowed": True,
        #             "ocoAllowed": True,
        #             "quoteOrderQtyMarketAllowed": True,
        #             "isSpotTradingAllowed": True,
        #             "isMarginTradingAllowed": True,
        #             "filters": [],
        #             "permissions": [
        #                 "SPOT",
        #                 "MARGIN"
        #             ]
        #         },
        #         {
        #             "symbol": "BNBBTC",
        #             "status": "TRADING",
        #             "baseAsset": "BNB",
        #             "baseAssetPrecision": 8,
        #             "quoteAsset": "BTC",
        #             "quotePrecision": 8,
        #             "quoteAssetPrecision": 8,
        #             "baseCommissionPrecision": 8,
        #             "quoteCommissionPrecision": 8,
        #             "orderTypes": [
        #                 "LIMIT",
        #                 "LIMIT_MAKER",
        #                 "MARKET",
        #                 "STOP_LOSS_LIMIT",
        #                 "TAKE_PROFIT_LIMIT"
        #             ],
        #             "icebergAllowed": True,
        #             "ocoAllowed": True,
        #             "quoteOrderQtyMarketAllowed": True,
        #             "isSpotTradingAllowed": True,
        #             "isMarginTradingAllowed": True,
        #             "filters": [],
        #             "permissions": [
        #                 "MARGIN"
        #             ]
        #         },
        #     ]
        # }

        mock_response: ArrayType = [{
            "id": "btcusdt",
            "name": "BTC/USDT",
            "base_unit": "btc",
            "quote_unit": "usdt",
            "min_price": "0.01",
            "max_price": "0.0",
            "min_amount": "0.001",
                    "amount_precision": 3,
                    "price_precision": 3,
                    "state": "enabled",
                    "buy_crypto_only": False,
                    "disable_sell": False
        }, {
            "id": "btceur",
            "name": "BTC/EUR",
            "base_unit": "btc",
            "quote_unit": "eur",
            "min_price": "0.001",
            "max_price": "0.0",
            "min_amount": "0.001",
            "amount_precision": 3,
            "price_precision": 3,
            "state": "enabled",
            "buy_crypto_only": False,
            "disable_sell": False
        }, {
            "id": "btcczk",
            "name": "BTC/CZK",
            "base_unit": "btc",
            "quote_unit": "czk",
            "min_price": "0.001",
            "max_price": "0.0",
            "min_amount": "0.0001",
            "amount_precision": 4,
            "price_precision": 3,
            "state": "enabled",
            "buy_crypto_only": False,
            "disable_sell": False
        }, {
            "id": "dxfczk",
            "name": "DXF/CZK",
            "base_unit": "dxf",
            "quote_unit": "czk",
            "min_price": "0.00001",
            "max_price": "0.0",
            "min_amount": "1000.0",
            "amount_precision": 2,
            "price_precision": 5,
            "state": "enabled",
            "buy_crypto_only": False,
            "disable_sell": False
        }, {
            "id": "dxfusdt",
            "name": "DXF/USDT",
            "base_unit": "dxf",
            "quote_unit": "usdt",
            "min_price": "0.001",
            "max_price": "0.0",
            "min_amount": "10.0",
            "amount_precision": 3,
            "price_precision": 6,
            "state": "enabled",
            "buy_crypto_only": False,
            "disable_sell": False
        }, {
            "id": "vrczk",
            "name": "VR/CZK",
            "base_unit": "vr",
            "quote_unit": "czk",
            "min_price": "0.00001",
            "max_price": "0.0",
            "min_amount": "300.0",
            "amount_precision": 3,
            "price_precision": 5,
            "state": "enabled",
            "buy_crypto_only": False,
            "disable_sell": False
        }]

        mock_api.get(url, body=json.dumps(mock_response))

        result: Dict[str] = self.async_run_with_timeout(
            self.data_source.fetch_trading_pairs(time_synchronizer=self.time_synchronizer)
        )

        self.assertEqual(6, len(result))
        self.assertIn("btc-usdt", result)
        self.assertIn("btc-czk", result)
        self.assertNotIn("eth-czk", result)

    @aioresponses()
    def test_fetch_trading_pairs_exception_raised(self, mock_api):
        DexfinAPIOrderBookDataSource._trading_pair_symbol_map = {}

        url = web_utils.public_rest_url(path_url=CONSTANTS.EXCHANGE_INFO_PATH_URL, base_url=self.base_url)
        regex_url = re.compile(f"^{url}".replace(".", r"\.").replace("?", r"\?"))

        mock_api.get(regex_url, exception=Exception)

        result: Dict[str] = self.async_run_with_timeout(
            self.data_source.fetch_trading_pairs(time_synchronizer=self.time_synchronizer)
        )

        self.assertEqual(0, len(result))

    @aioresponses()
    def test_get_snapshot_successful(self, mock_api):
        url = web_utils.public_rest_url(path_url=CONSTANTS.SNAPSHOT_PATH_URL.format("([A-Za-z]*)"), base_url=self.base_url)
        # regex_url = url
        # regex_url = re.compile(f"^{url}".replace(".", r"\.").replace("?", r"\?"))
        regex_url = re.compile(f"^{url}")

        mock_api.get(regex_url, body=json.dumps(self._snapshot_response()))

        result: Dict[str, Any] = self.async_run_with_timeout(
            self.data_source.get_snapshot(self.trading_pair), 1000
        )

        self.assertEqual(self._snapshot_response(), result)

    @aioresponses()
    def test_get_snapshot_catch_exception(self, mock_api):
        url = web_utils.public_rest_url(path_url=CONSTANTS.SNAPSHOT_PATH_URL.format("([A-Za-z]*)"), base_url=self.base_url)
        # regex_url = re.compile(f"^{url}".replace(".", r"\.").replace("?", r"\?"))
        regex_url = re.compile(f"^{url}")

        mock_api.get(regex_url, status=400)
        with self.assertRaises(IOError):
            self.async_run_with_timeout(
                self.data_source.get_snapshot(self.trading_pair)
            )

    @aioresponses()
    def test_get_new_order_book(self, mock_api):
        url = web_utils.public_rest_url(path_url=CONSTANTS.SNAPSHOT_PATH_URL.format("([A-Za-z]*)"), base_url=self.base_url)
        # regex_url = re.compile(f"^{url}".replace(".", r"\.").replace("?", r"\?"))
        regex_url = re.compile(f"^{url}")

        mock_response: Dict[str, Any] = {
            "timestamp": 1,
            "bids": [
                [
                    "4.00000000",
                    "431.00000000"
                ]
            ],
            "asks": [
                [
                    "4.00000200",
                    "12.00000000"
                ]
            ]
        }
        mock_api.get(regex_url, body=json.dumps(mock_response))

        result: OrderBook = self.async_run_with_timeout(
            self.data_source.get_new_order_book(self.trading_pair)
        )

        self.assertEqual(1, result.snapshot_uid)

    # @patch("aiohttp.ClientSession.ws_connect", new_callable=AsyncMock)
    # def test_listen_for_subscriptions_subscribes_to_trades_and_order_diffs(self, ws_connect_mock):
    #     ws_connect_mock.return_value = self.mocking_assistant.create_websocket_mock()

    #     result_subscribe_trades = {
    #         "result": None,
    #         "id": 1
    #     }
    #     result_subscribe_diffs = {
    #         "result": None,
    #         "id": 2
    #     }

    #     self.mocking_assistant.add_websocket_aiohttp_message(
    #         websocket_mock=ws_connect_mock.return_value,
    #         message=json.dumps(result_subscribe_trades))
    #     self.mocking_assistant.add_websocket_aiohttp_message(
    #         websocket_mock=ws_connect_mock.return_value,
    #         message=json.dumps(result_subscribe_diffs))

    #     self.listening_task = self.ev_loop.create_task(self.data_source.listen_for_subscriptions())

    #     self.mocking_assistant.run_until_all_aiohttp_messages_delivered(ws_connect_mock.return_value)

    #     sent_subscription_messages = self.mocking_assistant.json_messages_sent_through_websocket(
    #         websocket_mock=ws_connect_mock.return_value)

    #     self.assertEqual(2, len(sent_subscription_messages))
    #     expected_trade_subscription = {
    #         "method": "SUBSCRIBE",
    #         "params": [f"{self.ex_trading_pair.lower()}@trade"],
    #         "id": 1}
    #     self.assertEqual(expected_trade_subscription, sent_subscription_messages[0])
    #     expected_diff_subscription = {
    #         "method": "SUBSCRIBE",
    #         "params": [f"{self.ex_trading_pair.lower()}@depth@100ms"],
    #         "id": 2}
    #     self.assertEqual(expected_diff_subscription, sent_subscription_messages[1])

    #     self.assertTrue(self._is_logged(
    #         "INFO",
    #         "Subscribed to public order book and trade channels..."
    #     ))

    # @patch("hummingbot.core.data_type.order_book_tracker_data_source.OrderBookTrackerDataSource._sleep")
    # @patch("aiohttp.ClientSession.ws_connect")
    # def test_listen_for_subscriptions_raises_cancel_exception(self, mock_ws, _: AsyncMock):
    #     mock_ws.side_effect = asyncio.CancelledError

    #     with self.assertRaises(asyncio.CancelledError):
    #         self.listening_task = self.ev_loop.create_task(self.data_source.listen_for_subscriptions())
    #         self.async_run_with_timeout(self.listening_task)

    # @patch("hummingbot.core.data_type.order_book_tracker_data_source.OrderBookTrackerDataSource._sleep")
    # @patch("aiohttp.ClientSession.ws_connect", new_callable=AsyncMock)
    # def test_listen_for_subscriptions_logs_exception_details(self, mock_ws, sleep_mock):
    #     mock_ws.side_effect = Exception("TEST ERROR.")
    #     sleep_mock.side_effect = lambda _: self._create_exception_and_unlock_test_with_event(asyncio.CancelledError())

    #     self.listening_task = self.ev_loop.create_task(self.data_source.listen_for_subscriptions())

    #     self.async_run_with_timeout(self.resume_test_event.wait())

    #     self.assertTrue(
    #         self._is_logged(
    #             "ERROR",
    #             "Unexpected error occurred when listening to order book streams. Retrying in 5 seconds..."))

    def test_subscribe_channels_raises_cancel_exception(self):
        mock_ws = MagicMock()
        mock_ws.send.side_effect = asyncio.CancelledError

        with self.assertRaises(asyncio.CancelledError):
            self.listening_task = self.ev_loop.create_task(self.data_source._subscribe_channels(mock_ws))
            self.async_run_with_timeout(self.listening_task)

    def test_subscribe_channels_raises_exception_and_logs_error(self):
        mock_ws = MagicMock()
        mock_ws.send.side_effect = Exception("Test Error")

        with self.assertRaises(Exception):
            self.listening_task = self.ev_loop.create_task(self.data_source._subscribe_channels(mock_ws))
            self.async_run_with_timeout(self.listening_task)

        self.assertTrue(
            self._is_logged("ERROR", "Unexpected error occurred subscribing to order book trading and delta streams...")
        )

    def test_listen_for_trades_cancelled_when_listening(self):
        mock_queue = MagicMock()
        mock_queue.get.side_effect = asyncio.CancelledError()
        self.data_source._message_queue[CONSTANTS.TRADE_EVENT_TYPE] = mock_queue

        msg_queue: asyncio.Queue = asyncio.Queue()

        with self.assertRaises(asyncio.CancelledError):
            self.listening_task = self.ev_loop.create_task(
                self.data_source.listen_for_trades(self.ev_loop, msg_queue)
            )
            self.async_run_with_timeout(self.listening_task)

    def test_listen_for_trades_logs_exception(self):
        incomplete_resp = {
            "m": 1,
            "i": 2,
        }

        mock_queue = AsyncMock()
        mock_queue.get.side_effect = [incomplete_resp, asyncio.CancelledError()]
        self.data_source._message_queue[CONSTANTS.TRADE_EVENT_TYPE] = mock_queue

        msg_queue: asyncio.Queue = asyncio.Queue()

        self.listening_task = self.ev_loop.create_task(
            self.data_source.listen_for_trades(self.ev_loop, msg_queue)
        )

        try:
            self.async_run_with_timeout(self.listening_task)
        except asyncio.CancelledError:
            pass

        self.assertTrue(
            self._is_logged("ERROR", "Unexpected error when processing public trade updates from exchange"))

    def test_listen_for_trades_successful(self):
        mock_queue = AsyncMock()
        mock_queue.get.side_effect = [self._trade_update_event(), asyncio.CancelledError()]
        self.data_source._message_queue[CONSTANTS.TRADE_EVENT_TYPE] = mock_queue

        msg_queue: asyncio.Queue = asyncio.Queue()

        try:
            self.listening_task = self.ev_loop.create_task(
                self.data_source.listen_for_trades(self.ev_loop, msg_queue)
            )
        except asyncio.CancelledError:
            pass

        msg: OrderBookMessage = self.async_run_with_timeout(msg_queue.get())

        self.assertTrue(12345, msg.trade_id)

    def test_listen_for_order_book_diffs_cancelled(self):
        mock_queue = AsyncMock()
        mock_queue.get.side_effect = asyncio.CancelledError()
        self.data_source._message_queue[CONSTANTS.DIFF_EVENT_TYPE] = mock_queue

        msg_queue: asyncio.Queue = asyncio.Queue()

        with self.assertRaises(asyncio.CancelledError):
            self.listening_task = self.ev_loop.create_task(
                self.data_source.listen_for_order_book_diffs(self.ev_loop, msg_queue)
            )
            self.async_run_with_timeout(self.listening_task)

    def test_listen_for_order_book_diffs_logs_exception(self):
        incomplete_resp = {
            "m": 1,
            "i": 2,
        }

        mock_queue = AsyncMock()
        mock_queue.get.side_effect = [incomplete_resp, asyncio.CancelledError()]
        self.data_source._message_queue[CONSTANTS.DIFF_EVENT_TYPE] = mock_queue

        msg_queue: asyncio.Queue = asyncio.Queue()

        self.listening_task = self.ev_loop.create_task(
            self.data_source.listen_for_order_book_diffs(self.ev_loop, msg_queue)
        )

        try:
            self.async_run_with_timeout(self.listening_task)
        except asyncio.CancelledError:
            pass

        self.assertTrue(
            self._is_logged("ERROR", "Unexpected error when processing public order book updates from exchange"))

    # def test_listen_for_order_book_diffs_successful(self):
    #     mock_queue = AsyncMock()
    #     mock_queue.get.side_effect = [self._order_diff_event(), asyncio.CancelledError()]
    #     self.data_source._message_queue[CONSTANTS.DIFF_EVENT_TYPE] = mock_queue

    #     msg_queue: asyncio.Queue = asyncio.Queue()

    #     try:
    #         self.listening_task = self.ev_loop.create_task(
    #             self.data_source.listen_for_order_book_diffs(self.ev_loop, msg_queue)
    #         )
    #     except asyncio.CancelledError:
    #         pass

    #     msg: OrderBookMessage = self.async_run_with_timeout(msg_queue.get())

    #     self.assertTrue(12345, msg.update_id)

    @aioresponses()
    def test_listen_for_order_book_snapshots_cancelled_when_fetching_snapshot(self, mock_api):
        url = web_utils.public_rest_url(path_url=CONSTANTS.SNAPSHOT_PATH_URL.format("([A-Za-z]*)"), base_url=self.base_url)
        # regex_url = re.compile(f"^{url}".replace(".", r"\.").replace("?", r"\?"))
        regex_url = re.compile(f"^{url}")

        mock_api.get(regex_url, exception=asyncio.CancelledError)

        with self.assertRaises(asyncio.CancelledError):
            self.async_run_with_timeout(
                self.data_source.listen_for_order_book_snapshots(self.ev_loop, asyncio.Queue())
            )

    @aioresponses()
    @patch("hummingbot.connector.exchange.dexfin.dexfin_api_order_book_data_source"
           ".DexfinAPIOrderBookDataSource._sleep")
    def test_listen_for_order_book_snapshots_log_exception(self, mock_api, sleep_mock):
        msg_queue: asyncio.Queue = asyncio.Queue()
        sleep_mock.side_effect = lambda _: self._create_exception_and_unlock_test_with_event(asyncio.CancelledError())

        url = web_utils.public_rest_url(path_url=CONSTANTS.SNAPSHOT_PATH_URL.format("([A-Za-z]*)"), base_url=self.base_url)
        # regex_url = re.compile(f"^{url}".replace(".", r"\.").replace("?", r"\?"))
        regex_url = re.compile(f"^{url}")

        mock_api.get(regex_url, exception=Exception)

        self.listening_task = self.ev_loop.create_task(
            self.data_source.listen_for_order_book_snapshots(self.ev_loop, msg_queue)
        )
        self.async_run_with_timeout(self.resume_test_event.wait())

        self.assertTrue(
            self._is_logged("ERROR", f"Unexpected error fetching order book snapshot for {self.trading_pair}."))

    @aioresponses()
    def test_listen_for_order_book_snapshots_successful(self, mock_api, ):
        msg_queue: asyncio.Queue = asyncio.Queue()
        url = web_utils.public_rest_url(path_url=CONSTANTS.SNAPSHOT_PATH_URL.format("([A-Za-z]*)"), base_url=self.base_url)
        # regex_url = re.compile(f"^{url}".replace(".", r"\.").replace("?", r"\?"))
        regex_url = re.compile(f"^{url}")

        mock_api.get(regex_url, body=json.dumps(self._snapshot_response()))

        self.listening_task = self.ev_loop.create_task(
            self.data_source.listen_for_order_book_snapshots(self.ev_loop, msg_queue)
        )

        msg: OrderBookMessage = self.async_run_with_timeout(msg_queue.get())

        self.assertEqual(1656483612, msg.update_id)
