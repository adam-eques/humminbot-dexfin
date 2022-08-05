import asyncio
import hashlib
import hmac
from copy import copy
from pprint import pprint
from unittest import TestCase
from unittest.mock import MagicMock

from typing_extensions import Awaitable

from hummingbot.connector.exchange.dexfin.dexfin_auth import DexfinAuth
from hummingbot.connector.time_synchronizer import TimeSynchronizer
from hummingbot.core.web_assistant.connections.data_types import RESTMethod, RESTRequest


class DexfinAuthTests(TestCase):

    def setUp(self) -> None:
        self._api_key = "6d999b5beaa58452"
        self._secret = "d1598e6f226b836b77cb29d833190708vvvvv"

    def async_run_with_timeout(self, coroutine: Awaitable, timeout: float = 1):
        ret = asyncio.get_event_loop().run_until_complete(asyncio.wait_for(coroutine, timeout))
        return ret

    def test_rest_authenticate(self):
        now = 1234567890.000

        mock_time_provider = MagicMock()
        mock_time_provider.time.return_value = now

        auth = DexfinAuth(api_key=self._api_key, secret_key=self._secret, time_provider=mock_time_provider)
        request = RESTRequest(method=RESTMethod.GET, params={}, is_auth_required=True)
        # auth.rest_authenticate(request).__await__()
        configured_request = self.async_run_with_timeout(auth.rest_authenticate(request))

        # full_params.update({"X-Auth-Nonce": 1234567890000})
        # encoded_params = "&".join([f"{key}={value}" for key, value in full_params.items()])
        expected_signature = hmac.new(
            self._secret.encode("utf-8"),
            (str(int(now)) + self._api_key).encode("utf8"),
            hashlib.sha256).hexdigest()
        self.assertEqual(str(int(now)), configured_request.headers["X-Auth-Nonce"])
        self.assertEqual(expected_signature, configured_request.headers["X-Auth-Signature"])
        self.assertEqual(self._api_key, configured_request.headers["X-Auth-Apikey"])
        