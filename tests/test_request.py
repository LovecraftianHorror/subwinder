from datetime import datetime as dt
from multiprocessing.dummy import Pool
from unittest.mock import call, patch

import pytest  # type: ignore

from subwinder._request import Endpoints, _client, request
from subwinder.exceptions import SubServerError


def test__request():
    RESP = {"status": "200 OK", "data": "The data!", "seconds": "0.15"}
    with patch.object(_client, "ServerInfo", return_value=RESP) as mocked:
        # Response should be passed through on success
        assert request(Endpoints.SERVER_INFO, None) == RESP
        mocked.assert_called_once_with()


# Note: this test takes a bit of time because of the delayed API request retry
@pytest.mark.slow
def test_retry_on_fail():
    CALLS = [
        call("<token>", "arg1", "arg2"),
        call("<token>", "arg1", "arg2"),
    ]
    RESPS = [
        {"status": "429 Too many requests", "seconds": "0.10"},
        {"status": "200 OK", "data": "The data!", "seconds": "0.15"},
    ]
    with patch.object(_client, "GetUserInfo") as mocked:
        mocked.side_effect = RESPS
        assert request(Endpoints.GET_USER_INFO, "<token>", "arg1", "arg2") == RESPS[1]
        mocked.assert_has_calls(CALLS)


@pytest.mark.slow
def test_request_timeout():
    # Requests take a bit to timeout so we're just gonna run all of them simultaneously
    with Pool(len(Endpoints)) as pool:
        pool.map(_test_request_timeout, list(Endpoints))


def _test_request_timeout(endpoint):
    RATE_LIMIT_SECONDS = 10
    BAD_RESP = {"status": "429 Too many requests", "seconds": "0.10"}

    # Only returns a bad response so keeps retrying till timeout
    with patch.object(_client, endpoint.value, return_value=BAD_RESP):
        start = dt.now()
        with pytest.raises(SubServerError):
            request(endpoint, "<token>")

        # `request` should keep trying long enough for the rate limit to expire
        assert (dt.now() - start).total_seconds() > RATE_LIMIT_SECONDS
