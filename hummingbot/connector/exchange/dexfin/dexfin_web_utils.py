from pprint import pprint
from typing import Any, Callable, Dict, Optional

import hummingbot.connector.exchange.dexfin.dexfin_constants as CONSTANTS
import hummingbot.connector.exchange.dexfin.dexfin_utils as utils
from hummingbot.connector.time_synchronizer import TimeSynchronizer
from hummingbot.connector.utils import TimeSynchronizerRESTPreProcessor
from hummingbot.core.api_throttler.async_throttler import AsyncThrottler
from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.connections.data_types import RESTMethod, RESTRequest
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory


def public_rest_url(path_url: str, base_url: str = CONSTANTS.REST_URL) -> str:
    """
    Creates a full URL for provided public REST endpoint
    :param path_url: a public REST endpoint
    :param domain: the Binance domain to connect to ("com" or "us"). The default value is "com"
    :return: the full URL to the endpoint
    """
    return base_url + path_url


def private_rest_url(path_url: str, base_url: str = CONSTANTS.REST_URL) -> str:
    """
    Creates a full URL for provided private REST endpoint
    :param path_url: a private REST endpoint
    :param domain: the Binance domain to connect to ("com" or "us"). The default value is "com"
    :return: the full URL to the endpoint
    """
    return base_url + path_url


def build_api_factory(
        throttler: Optional[AsyncThrottler] = None,
        time_synchronizer: Optional[TimeSynchronizer] = None,
        base_url: str = CONSTANTS.REST_URL,
        time_provider: Optional[Callable] = None,
        auth: Optional[AuthBase] = None, ) -> WebAssistantsFactory:
    time_synchronizer = time_synchronizer or TimeSynchronizer()
    time_provider = time_provider or (lambda: get_current_server_time(
        throttler=throttler,
        base_url=base_url,
    ))
    api_factory = WebAssistantsFactory(
        auth=auth,
        rest_pre_processors=[
            TimeSynchronizerRESTPreProcessor(synchronizer=time_synchronizer, time_provider=time_provider),
        ])
    return api_factory


def build_api_factory_without_time_synchronizer_pre_processor() -> WebAssistantsFactory:
    api_factory = WebAssistantsFactory()
    return api_factory


def create_throttler() -> AsyncThrottler:
    # return AsyncThrottler(CONSTANTS.RATE_LIMITS)
    return None


async def api_request(path: str,
                      api_factory: Optional[WebAssistantsFactory] = None,
                      throttler: Optional[AsyncThrottler] = None,
                      time_synchronizer: Optional[TimeSynchronizer] = None,
                      base_url: str = CONSTANTS.REST_URL,
                      params: Optional[Dict[str, Any]] = None,
                      data: Optional[Dict[str, Any]] = None,
                      method: RESTMethod = RESTMethod.GET,
                      is_auth_required: bool = False,
                      return_err: bool = False,
                      limit_id: Optional[str] = None,
                      timeout: Optional[float] = None,
                      headers: Dict[str, Any] = {}):
    throttler = throttler or create_throttler()
    time_synchronizer = time_synchronizer or TimeSynchronizer()

    # If api_factory is not provided a default one is created
    # The default instance has no authentication capabilities and all authenticated requests will fail
    api_factory = api_factory or build_api_factory(
        throttler=throttler,
        time_synchronizer=time_synchronizer,
        base_url=base_url,
    )
    rest_assistant = await api_factory.get_rest_assistant()

    local_headers = {
        "Content-Type": "application/json" if method == RESTMethod.POST else "application/x-www-form-urlencoded"}
    local_headers.update(headers)
    if is_auth_required:
        url = private_rest_url(path, base_url=base_url)
    else:
        url = public_rest_url(path, base_url=base_url)

    request = RESTRequest(
        method=method,
        url=url,
        params=params,
        data=data,
        headers=local_headers,
        is_auth_required=is_auth_required,
        throttler_limit_id=limit_id if limit_id else path
    )

    # async with throttler.execute_task(limit_id=limit_id if limit_id else path):
    response = await rest_assistant.call(request=request, timeout=timeout)

    if not (response.status == 200 or response.status == 201):
        # print(response.json())
        if return_err:
            error_response = await response.json()
            return error_response
        else:
            error_response = await response.text()
            if error_response is not None and "code" in error_response and "msg" in error_response:
                raise IOError(f"The request to Binance failed. Error: {error_response}. Request: {request}")
            else:
                raise IOError(f"Error executing request {method.name} {path}. "
                              f"HTTP status is {response.status}. "
                              f"Error: {error_response}")

    return await response.json()


async def get_current_server_time(
        throttler: Optional[AsyncThrottler] = None,
        base_url: str = CONSTANTS.REST_URL,
) -> float:
    api_factory = build_api_factory_without_time_synchronizer_pre_processor()
    response = await api_request(
        path=CONSTANTS.SERVER_TIME_PATH_URL,
        api_factory=api_factory,
        throttler=throttler,
        base_url=base_url,
        method=RESTMethod.GET)

    server_time = utils.iso_datetime_to_timestamp(response) * 1e3
    return server_time
