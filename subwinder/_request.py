from datetime import datetime
import time
from xmlrpc.client import ServerProxy, Transport, ProtocolError

from subwinder.constants import _API_BASE, _REPO_URL
from subwinder.exceptions import (
    SubAuthError,
    SubDownloadError,
    SubLibError,
    SubServerError,
    SubUploadError,
)


# Responses 403, 404, 405, 406, 409 should be prevented by API
_API_ERROR_MAP = {
    "401": SubAuthError,
    "402": SubUploadError,
    "407": SubDownloadError,
    "408": SubLibError,
    "410": SubLibError,
    "411": SubAuthError,
    "412": SubUploadError,
    "413": SubLibError,
    "414": SubAuthError,
    "415": SubAuthError,
    "416": SubUploadError,
    "429": SubServerError,
    "503": SubServerError,
    "506": SubServerError,
    "520": SubServerError,
}

_API_PROTOCOL_ERR_MAP = {
    503: "503 Service Unavailable",
    506: "506 Server under maintenance",
    520: "520 Unknown internal error",
}

_client = ServerProxy(_API_BASE, allow_none=True, transport=Transport())


# TODO: give a way to let lib user to set `TIMEOUT`?
def request(method, token, *params):
    TIMEOUT = 15
    DELAY_FACTOR = 2
    current_delay = 1.5
    start = datetime.now()

    # Keep retrying if status code indicates rate limiting (429) or server error (5XX)
    # until the `TIMEOUT` is hit
    while True:
        try:
            if method in ("AutoUpdate", "GetSubLanguages", "LogIn", "ServerInfo"):
                # Flexible way to call method while reducing error handling
                resp = getattr(_client, method)(*params)
            else:
                # Use the token if it's defined
                resp = getattr(_client, method)(token, *params)
        except ProtocolError as err:
            # Try handling the `ProtocolError` appropriately
            if err.errcode in _API_PROTOCOL_ERR_MAP:
                resp = {"status": _API_PROTOCOL_ERR_MAP[err.errcode]}
            else:
                # Unexpected `ProtocolError`
                raise SubLibError(
                    "The server returned an unhandled protocol error. Please raise an"
                    f" issue in the repo ({_REPO_URL}) so that this can be handled in"
                    f" the future\nProtocolError: {err}"
                )

        # Some endpoints don't return a status when "OK" like GetSubLanguages or
        # ServerInfo, so force the status if it's missing
        if "status" not in method:
            resp["status"] = "200 OK"

        if "status" not in resp:
            raise SubLibError(
                f'"{method}" should return a status and didn\'t, consider raising an'
                f" issue at {_REPO_URL} to address this"
            )

        status_code = resp["status"][:3]
        status_msg = resp["status"][4:]

        # Retry if rate limit was hit (429) or server error (5XX), otherwise handle
        # appropriately
        if status_code not in ("429", "503", "506", "520"):
            break

        # Server under heavy load, wait and retry
        remaining_time = TIMEOUT - (datetime.now() - start).total_seconds()
        if remaining_time <= current_delay:
            # Not enough time to try again so go ahead and `break`
            break

        time.sleep(current_delay)
        current_delay *= DELAY_FACTOR

    # Handle the response
    if status_code == "200":
        return resp
    elif status_code in _API_ERROR_MAP:
        raise _API_ERROR_MAP[status_code](status_msg)
    else:
        raise SubLibError(
            "the API returned an unhandled response, consider raising an issue to"
            f" address this at {_REPO_URL}\nResponse status: '{resp['status']}'"
        )