import time
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from xml.parsers.expat import ExpatError
from xmlrpc.client import ProtocolError, ServerProxy, Transport

from subwinder._constants import API_BASE, REPO_URL
from subwinder.exceptions import (
    SubAuthError,
    SubDownloadError,
    SubLibError,
    SubServerError,
    SubUploadError,
)


# The names of all the different endpoints exposed by opensubtitles
class Endpoints(Enum):
    ADD_COMMENT = "AddComment"
    ADD_REQUEST = "AddRequest"
    AUTO_UPDATE = "AutoUpdate"
    CHECK_MOVIE_HASH = "CheckMovieHash"
    CHECK_MOVIE_HASH2 = "CheckMovieHash2"
    CHECK_SUB_HASH = "CheckSubHash"
    DETECT_LANGUAGE = "DetectLanguage"
    DOWNLOAD_SUBTITLES = "DownloadSubtitles"
    GET_AVAILABLE_TRANSLATIONS = "GetAvailableTranslations"
    GET_COMMENTS = "GetComments"
    GET_IMDB_MOVIE_DETAILS = "GetIMDBMovieDetails"
    GET_SUB_LANGUAGES = "GetSubLanguages"
    GET_TRANSLATION = "GetTranslation"
    GET_USER_INFO = "GetUserInfo"
    GUESS_MOVIE_FROM_STRING = "GuessMovieFromString"
    INSERT_MOVIE = "InsertMovie"
    INSERT_MOVIE_HASH = "InsertMovieHash"
    LOG_IN = "LogIn"
    LOG_OUT = "LogOut"
    NO_OPERATION = "NoOperation"
    PREVIEW_SUBTITLES = "PreviewSubtitles"
    QUICK_SUGGEST = "QuickSuggest"
    REPORT_WRONG_IMDB_MOVIE = "ReportWrongImdbMovie"
    REPORT_WRONG_MOVIE_HASH = "ReportWrongMovieHash"
    SEARCH_MOVIES_ON_IMDB = "SearchMoviesOnIMDB"
    SEARCH_SUBTITLES = "SearchSubtitles"
    SEARCH_TO_MAIL = "SearchToMail"
    SET_SUBSCRIBE_URL = "SetSubscribeUrl"
    SERVER_INFO = "ServerInfo"
    SUBSCRIBE_TO_HASH = "SubscribeToHash"
    SUBTITLES_VOTE = "SubtitlesVote"
    SUGGEST_MOVIE = "SuggestMovie"
    TRY_UPLOAD_SUBTITLES = "TryUploadSubtitles"
    UPLOAD_SUBTITLES = "UploadSubtitles"


_TOKENLESS_ENDPOINTS = [
    Endpoints.AUTO_UPDATE,
    Endpoints.GET_SUB_LANGUAGES,
    Endpoints.LOG_IN,
    Endpoints.SERVER_INFO,
]


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

_client = ServerProxy(API_BASE, allow_none=True, transport=Transport())


# TODO: better define the values xmlrpc takes and gives to avoid any here
# TODO: give a way to let lib user to set `TIMEOUT`?
def request(endpoint: Endpoints, token: Optional[str], *params: Any) -> dict:
    """
    Function to allow for robust and reusable calls to the XMLRPC API. `endpoint`
    is the `Endpoint` that you want to use from the opensubtitles API. `token` is the
    auth token that is used for any user-authenticated calls. `*params` are any
    additional parameters to pass to the API.
    Note: Retrying with exponential backoff and exposing appropriate errors are all
    handled automatically.
    """
    TIMEOUT = 15
    DELAY_FACTOR = 2
    current_delay = 1.5
    start = datetime.now()

    # Keep retrying if status code indicates rate limiting (429) or server error (5XX)
    # until the `TIMEOUT` is hit
    while True:
        try:
            if endpoint in _TOKENLESS_ENDPOINTS:
                # Flexible way to call method while reducing error handling
                resp = getattr(_client, endpoint.value)(*params)
            else:
                # Use the token if it's defined
                resp = getattr(_client, endpoint.value)(token, *params)
        except ExpatError:
            # So an expat error was an error parsing the xml response. I believe this is
            # hit when the API is having problems and sends a plaintext message instead
            # of valid XML
            raise SubServerError(
                "The server sent invalid XML. Likely due to temporary server issues."
            )
        except ProtocolError as err:
            # Try handling the `ProtocolError` appropriately
            if err.errcode in _API_PROTOCOL_ERR_MAP:
                resp = {"status": _API_PROTOCOL_ERR_MAP[err.errcode]}
            else:
                # Unexpected `ProtocolError`
                raise SubLibError(
                    "The server returned an unhandled protocol error. Please raise an"
                    f" issue in the repo ({REPO_URL}) so that this can be handled in"
                    f" the future\nProtocolError: {err}"
                )

        # Some endpoints don't return a status when "OK" like GetSubLanguages or
        # ServerInfo, so force the status if it's missing
        if "status" not in resp:
            resp["status"] = "200 OK"

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
            f" address this at {REPO_URL}\nResponse status: '{resp['status']}'"
        )
