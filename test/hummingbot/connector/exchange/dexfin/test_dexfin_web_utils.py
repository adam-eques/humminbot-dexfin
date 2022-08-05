import asyncio
import unittest

from typing_extensions import Awaitable

import hummingbot.connector.exchange.dexfin.dexfin_constants as CONSTANTS
from hummingbot.connector.exchange.dexfin import dexfin_web_utils as web_utils


class DexfinWebUtilsTest(unittest.TestCase):
    def test_public_rest_url(self):
        path_url = "/TEST_PATH"
        expected_url = CONSTANTS.REST_URL + path_url
        self.assertEqual(expected_url, web_utils.public_rest_url(path_url))

    def async_run_with_timeout(self, coroutine: Awaitable, timeout: float = 1):
        ret = asyncio.get_event_loop().run_until_complete(asyncio.wait_for(coroutine, timeout))
        return ret

    def test_private_rest_url(self):
        path_url = "/TEST_PATH"
        expected_url = CONSTANTS.REST_URL + path_url
        self.assertEqual(expected_url, web_utils.private_rest_url(path_url))

    def test_get_current_server_time(self):
        server_time = self.async_run_with_timeout(web_utils.get_current_server_time(), 1000)
        self.assertIsNotNone(server_time)
