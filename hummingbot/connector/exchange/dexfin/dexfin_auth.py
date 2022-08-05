import hashlib
import hmac
from collections import OrderedDict
from pprint import pprint
from typing import Any, Dict
from urllib.parse import urlencode

from hummingbot.connector.time_synchronizer import TimeSynchronizer
from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.connections.data_types import RESTMethod, RESTRequest, WSRequest


class DexfinAuth(AuthBase):

    def __init__(self, api_key: str, secret_key: str, time_provider: TimeSynchronizer):
        self.api_key = api_key
        self.secret_key = secret_key
        self.time_provider = time_provider

    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        """
        Adds the server time and the signature to the request, required for authenticated interactions. It also adds
        the required parameter in the request header.
        :param request: the request to be configured for authenticated interaction
        """
        headers = {}
        if request.headers is not None:
            headers.update(request.headers)
        headers.update(self.header_for_authentication())
        request.headers = headers

        return request

    async def ws_authenticate(self, request: WSRequest) -> WSRequest:
        """
        This method is intended to configure a websocket request to be authenticated. Binance does not use this
        functionality
        """
        return request  # pass-through

    def header_for_authentication(self) -> Dict[str, str]:
        nonce = str(int(self.time_provider.time()))
        pprint(nonce)
        signature = self._generate_signature(nonce)
        return {
            "X-Auth-Apikey": self.api_key,
            "X-Auth-Nonce": nonce,
            "X-Auth-Signature": signature
        }

    def _generate_signature(self, nonce: str) -> str:
        digest = hmac.new(self.secret_key.encode("utf8"), (nonce + self.api_key).encode("utf8"), hashlib.sha256).hexdigest()
        return digest
