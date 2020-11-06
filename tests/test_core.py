import json
import os
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import call, patch

import pytest  # type: ignore

from subwinder import AuthSubwinder, Subwinder
from subwinder._constants import Env
from subwinder._request import Endpoints
from subwinder.exceptions import SubAuthError, SubDownloadError
from subwinder.info import Comment, MovieInfo, TvSeriesInfo, UserInfo
from tests.constants import (
    DOWNLOAD_INFO,
    EPISODE_INFO1,
    FULL_USER_INFO1,
    MEDIA1,
    MOVIE_INFO1,
    SAMPLES_DIR,
    SEARCH_RESULT1,
    SEARCH_RESULT2,
    SERVER_INFO,
)


# TODO: do this with a fixture too?
def _dummy_auth_subwinder():
    return AuthSubwinder.__new__(AuthSubwinder)


# TODO: is this really required
def _standard_asw_mock(
    method, mocked_method, method_args, response, expected_call, ideal_result
):
    asw = _dummy_auth_subwinder()

    with patch.object(asw, mocked_method, return_value=response) as mocked:
        result = getattr(asw, method)(*method_args)

    mocked.assert_called_with(*expected_call)
    assert result == ideal_result


def test_daily_download_info():
    with (SAMPLES_DIR / "server_info.json").open() as f:
        RESP = json.load(f)
    IDEAL = DOWNLOAD_INFO

    with patch.object(Subwinder, "_request", return_value=RESP) as mocked:
        result = Subwinder().daily_download_info()

    assert result == IDEAL
    mocked.assert_called_once_with(Endpoints.SERVER_INFO)


def test_get_languages():
    sw = Subwinder()
    assert sw.get_languages() == [
        ("de", "ger", "German"),
        ("en", "eng", "English"),
        ("fr", "fre", "French"),
    ]


def test_server_info():
    with (SAMPLES_DIR / "server_info.json").open() as f:
        RESP = json.load(f)
    IDEAL = SERVER_INFO

    with patch.object(Subwinder, "_request", return_value=RESP) as mocked:
        result = Subwinder().server_info()

    assert result == IDEAL
    mocked.assert_called_once_with(Endpoints.SERVER_INFO)


# TODO: assert that _request isn't called for bad params?
# TODO: test correct case as well (assert token as well)
# XXX: ENV_VARS stuff is a bit messy here. try to clean up logic if possible
#      should probably be a fixture that wipes env vars in the beginning of all testing
def test_authsubwinder__init__():
    # Clear out env vars if set
    for variant in Env:
        if variant.value in os.environ:
            del os.environ[variant.value]

    bad_params = [
        # Empty creds
        [],
        # Missing both password and useragent
        ["<username>"],
        # Missing useragent
        ["<username>", "<password>"],
        # Invalid useragent
        ["<username>", "<password>", None],
    ]

    for params in bad_params:
        with pytest.raises(SubAuthError):
            AuthSubwinder(*params)


# TODO: Test creating an AuthSubwinder instead
def test__login():
    QUERIES = ("<username>", "<password>", "<useragent>")
    RESP = {"status": "200 OK", "token": "<token>"}
    CALL = (Endpoints.LOG_IN, "<username>", "<password>", "en", "<useragent>")

    _standard_asw_mock("_login", "_request", QUERIES, RESP, CALL, "<token>")


# TODO: This should be tested with `with` instead
def test__logout():
    QUERIES = ()
    RESP = {"status": "200 OK", "seconds": 0.055}
    CALL = [Endpoints.LOG_OUT]

    _standard_asw_mock("_logout", "_request", QUERIES, RESP, CALL, None)


def test_add_comment():
    QUERIES = (SEARCH_RESULT1, "bad comment", True)
    RESP = {"status": "200 OK", "seconds": "0.228"}
    CALL = (Endpoints.ADD_COMMENT, SEARCH_RESULT1.subtitles.id, "bad comment", True)

    _standard_asw_mock("add_comment", "_request", QUERIES, RESP, CALL, None)


def test_auto_update():
    PROGRAM_NAME = "SubDownloader"
    QUERIES = [PROGRAM_NAME]
    CALL = (Endpoints.AUTO_UPDATE, PROGRAM_NAME)
    with (SAMPLES_DIR / "auto_update.json").open() as f:
        RESP = json.load(f)

    _standard_asw_mock("auto_update", "_request", QUERIES, RESP, CALL, RESP)


def test_download_subtitles():
    BARE_PATH = SEARCH_RESULT1.media.get_dirname() / SEARCH_RESULT1.subtitles.filename
    BARE_QUERIES = [[SEARCH_RESULT1]]
    BARE_CALL = ([SEARCH_RESULT1.subtitles], [BARE_PATH])
    BARE_IDEAL = [BARE_PATH]

    FULL_PATH = Path("test dir") / "test file"
    FULL_QUERIES = [[SEARCH_RESULT1.subtitles], "test dir", "test file"]
    FULL_CALL = ([SEARCH_RESULT1.subtitles], [FULL_PATH])
    FULL_IDEAL = [FULL_PATH]
    RESP = None

    asw = _dummy_auth_subwinder()

    # Mock out the call to get remaining downloads as 200
    with patch.object(asw, "daily_download_info", return_value=DOWNLOAD_INFO):
        # Test sucessfully downloading with bare params
        with patch.object(asw, "_download_subtitles", return_value=RESP) as mocked:
            result = asw.download_subtitles(*BARE_QUERIES)
            mocked.assert_called_with(*BARE_CALL)
            assert result == BARE_IDEAL

            # Test successfully downloading with full params
            result = asw.download_subtitles(*FULL_QUERIES)
            mocked.assert_called_with(*FULL_CALL)
            assert result == FULL_IDEAL

        # Test failing from no `download_dir`
        temp_dirname = BARE_QUERIES[0][0].media.get_dirname()
        BARE_QUERIES[0][0].media.set_dirname(None)
        with pytest.raises(SubDownloadError):
            _ = asw.download_subtitles(*BARE_QUERIES)
        BARE_QUERIES[0][0].media.dirname = temp_dirname

        # Test failing from no `media_name` for `name_format`
        temp_filename = BARE_QUERIES[0][0].media.get_filename()
        BARE_QUERIES[0][0].media.set_filename(None)
        with pytest.raises(SubDownloadError):
            _ = asw.download_subtitles(*BARE_QUERIES, name_format="{media_name}")
    BARE_QUERIES[0][0].media.set_filename(temp_filename)


# TODO: combine the logic up above with down here
def test__download_subtitles():
    asw = _dummy_auth_subwinder()

    with (SAMPLES_DIR / "download_subtitles.json").open() as f:
        RESP = json.load(f)
    IDEAL_CONTENTS = (
        "Hello there, I'm that good ole compressed and encoded subtitle information"
        " that you so dearly want to save"
    )

    with TemporaryDirectory() as temp_dir:
        sub_path = Path(temp_dir) / "test download.txt"

        with patch.object(asw, "_request", return_value=RESP) as mocked:
            asw._download_subtitles([SEARCH_RESULT1.subtitles], [sub_path])

        mocked.assert_called_with(
            Endpoints.DOWNLOAD_SUBTITLES, [SEARCH_RESULT1.subtitles.file_id]
        )

        # Check the contents for the correct result
        with sub_path.open() as f:
            assert f.read() == IDEAL_CONTENTS


def test_get_comments():
    # Build up the empty `SearchResult`s and add the `subtitles.id`
    queries = [[SEARCH_RESULT1, SEARCH_RESULT2]]
    with (SAMPLES_DIR / "get_comments.json").open() as f:
        RESP = json.load(f)
    ideal_result = [
        [
            Comment(
                UserInfo("192696", "neo_rtr"),
                datetime(2008, 12, 14, 17, 20, 42),
                "Greate Work. thank you",
            )
        ],
        [
            Comment(
                UserInfo("745565", "pee-jay_cz"),
                datetime(2008, 12, 12, 15, 21, 48),
                "Thank you.",
            ),
            Comment(
                UserInfo("754781", "Guzeppi"),
                datetime(2008, 12, 12, 15, 51, 1),
                "You're welcome :)",
            ),
        ],
    ]
    CALL = (
        Endpoints.GET_COMMENTS,
        [SEARCH_RESULT1.subtitles.id, SEARCH_RESULT2.subtitles.id],
    )

    _standard_asw_mock("get_comments", "_request", queries, RESP, CALL, ideal_result)


def test_guess_media():
    asw = _dummy_auth_subwinder()

    QUERIES = [
        "heross01e08.avi",
        "Insurgent.2015.READNFO.CAM.AAC.x264-LEGi0N",
        "Night Watch",
        "Aliens 1080p BluRay AC3 x264-ETRG.mkv",
    ]
    # The calls are split due to batching
    CALLS = [
        call(Endpoints.GUESS_MOVIE_FROM_STRING, QUERIES[:3]),
        call(Endpoints.GUESS_MOVIE_FROM_STRING, QUERIES[3:]),
    ]
    IDEAL_RESULT = [
        TvSeriesInfo("Heroes", 2006, "0813715", None, None),
        MovieInfo("Insurgent", 2015, "2908446", None, None),
        MovieInfo("Nochnoy dozor", 2004, "0403358", None, None),
        MovieInfo("Aliens", 1986, "0090605", None, None),
    ]
    with (SAMPLES_DIR / "guess_media.json").open() as f:
        RESP = json.load(f)

    with patch.object(asw, "_request") as mocked:
        mocked.side_effect = RESP
        guesses = asw.guess_media(QUERIES)

    assert guesses == IDEAL_RESULT
    mocked.assert_has_calls(CALLS)

    # Now to test the edge cases
    EDGE_QUERIES = [
        "",
        "adsfkljadsf",
    ]
    CALL = (Endpoints.GUESS_MOVIE_FROM_STRING, EDGE_QUERIES)
    IDEAL_RESULT = [None, None]
    with (SAMPLES_DIR / "guess_media_edge_cases.json").open() as f:
        EDGE_RESP = json.load(f)

    with patch.object(asw, "_request") as mocked:
        mocked.side_effect = EDGE_RESP
        guesses = asw.guess_media(EDGE_QUERIES)

    assert guesses == IDEAL_RESULT
    mocked.assert_called_once_with(*CALL)


def test_ping():
    RESP = {"status": "200 OK", "seconds": "0.055"}
    CALL = [Endpoints.NO_OPERATION]

    _standard_asw_mock("ping", "_request", (), RESP, CALL, None)


def test_report_media():
    QUERY = [SEARCH_RESULT2]
    CALL = (Endpoints.REPORT_WRONG_MOVIE_HASH, SEARCH_RESULT2.subtitles.sub_to_movie_id)
    RESP = {"status": "200 OK", "seconds": "0.115"}

    _standard_asw_mock("report_media", "_request", QUERY, RESP, CALL, None)


def test_search_subtitles():
    QUERIES = [[(MEDIA1, "en"), (MOVIE_INFO1, "fr"), (EPISODE_INFO1, "de")]]
    CALL = [*QUERIES]
    # Just testing that the correct amount of `SearchResult`s are returned
    RESP = [
        [SEARCH_RESULT2],
        [SEARCH_RESULT2],
        [SEARCH_RESULT2],
    ]
    IDEAL = [
        SEARCH_RESULT2,
        SEARCH_RESULT2,
        SEARCH_RESULT2,
    ]

    # XXX: Test through to _request, not just to _search_subtitles_unranked
    _standard_asw_mock(
        "search_subtitles", "_search_subtitles_unranked", QUERIES, RESP, CALL, IDEAL
    )


# XXX: combine this with the above
def test__search_subtitles_unranked():
    QUERIES = [[(MEDIA1, "en")]]
    CALL = (
        Endpoints.SEARCH_SUBTITLES,
        [
            {
                "sublanguageid": "eng",
                "moviehash": "18379ac9af039390",
                "moviebytesize": "366876694",
            },
        ],
    )
    with (SAMPLES_DIR / "search_subtitles.json").open() as f:
        RESP = json.load(f)

    IDEAL = [[SEARCH_RESULT2]]

    _standard_asw_mock(
        "_search_subtitles_unranked", "_request", QUERIES, RESP, CALL, IDEAL
    )


def test_suggest_media():
    QUERY = ["matrix"]
    CALL = (Endpoints.SUGGEST_MOVIE, "matrix")
    with (SAMPLES_DIR / "suggest_media.json").open() as f:
        RESP = json.load(f)
    IDEAL = [
        MovieInfo("The Matrix", 1999, "0133093", None, None),
        MovieInfo("The Matrix Reloaded", 2003, "0234215", None, None),
    ]

    _standard_asw_mock("suggest_media", "_request", QUERY, RESP, CALL, IDEAL)


def test_user_info():
    CALL = [Endpoints.GET_USER_INFO]
    with (SAMPLES_DIR / "user_info.json").open() as f:
        RESP = json.load(f)
    IDEAL_RESULT = FULL_USER_INFO1

    _standard_asw_mock("user_info", "_request", (), RESP, CALL, IDEAL_RESULT)


def test_vote():
    INVALID_SCORES = [0, 11]
    VALID_SCORES = range(1, 10 + 1)
    with (SAMPLES_DIR / "vote.json").open() as f:
        RESP = json.load(f)

    # Test valid scores
    for score in VALID_SCORES:
        query = (SEARCH_RESULT1, score)
        call = (Endpoints.SUBTITLES_VOTE, SEARCH_RESULT1.subtitles.id, score)
        _standard_asw_mock("vote", "_request", query, RESP, call, None)

    # Test invalid scores
    for score in INVALID_SCORES:
        query = (SEARCH_RESULT1, score)
        call = (Endpoints.SUBTITLES_VOTE, SEARCH_RESULT1.subtitles.id, score)

        asw = _dummy_auth_subwinder()

        with patch.object(asw, "_request", return_value=RESP):
            with pytest.raises(ValueError):
                asw.vote(*query)


# XXX: this should really test to _request, not just _preview_subtitles
def test_preview_subtitles():
    QUERIES = [[SEARCH_RESULT1, SEARCH_RESULT2.subtitles]]
    CALL = [[SEARCH_RESULT1.subtitles.file_id, SEARCH_RESULT2.subtitles.file_id]]
    RESP = ["preview 1", "preview 2"]
    IDEAL = RESP

    _standard_asw_mock(
        "preview_subtitles", "_preview_subtitles", QUERIES, RESP, CALL, IDEAL
    )


# XXX: combine with the above
def test__preview_subtitles():
    QUERIES = [["1951976245"]]
    CALL = (Endpoints.PREVIEW_SUBTITLES, QUERIES[0])
    with (SAMPLES_DIR / "preview_subtitles.json").open() as f:
        RESP = json.load(f)

    IDEAL = ["1\r\n00:00:12,345 --> 00:01:23,456\r\nFirst subtitle\r\nblock"]

    _standard_asw_mock("_preview_subtitles", "_request", QUERIES, RESP, CALL, IDEAL)
