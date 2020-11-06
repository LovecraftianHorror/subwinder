import json
from datetime import datetime
from unittest.mock import patch

import pytest  # type: ignore

from subwinder.info import (
    Comment,
    EpisodeInfo,
    FullUserInfo,
    MediaInfo,
    MovieInfo,
    SearchResult,
    SubtitlesInfo,
    TvSeriesInfo,
    UserInfo,
    build_media_info,
)
from tests.constants import (
    EPISODE_INFO1,
    FULL_USER_INFO1,
    INFO_DIR,
    SAMPLES_DIR,
    SEARCH_RESULT2,
    SUBTITLES_INFO1,
    USER_INFO1,
)


def test_build_media_info():
    with (SAMPLES_DIR / "search_subtitles.json").open() as f:
        RESP = json.load(f)
    data = RESP["data"][0]

    # Test detecting the correct type of media
    with patch.object(EpisodeInfo, "from_data") as mocked:
        build_media_info(data)
        mocked.assert_called_once_with(data)

    data["MovieKind"] = "movie"
    with patch.object(MovieInfo, "from_data") as mocked:
        build_media_info(data)
        mocked.assert_called_once_with(data)

    data["MovieKind"] = "tv series"
    with patch.object(TvSeriesInfo, "from_data") as mocked:
        build_media_info(data)
        mocked.assert_called_once_with(data)


def test_UserInfo():
    DATA = {"UserID": "1332962", "UserNickName": "elderman"}

    assert UserInfo.from_data(DATA) == USER_INFO1


def test_FullUserInfo():
    with (INFO_DIR / "full_user_info.json").open() as f:
        DATA = json.load(f)

    assert FullUserInfo.from_data(DATA) == FULL_USER_INFO1


def test_Comment():
    with (INFO_DIR / "comment.json").open() as f:
        DATA = json.load(f)

    assert Comment.from_data(DATA) == Comment(
        UserInfo("<id>", "<name>"), datetime(2000, 1, 2, 3, 4, 5), "<comment>",
    )


def test_MediaInfo():
    with (INFO_DIR / "media_info.json").open() as f:
        DATA = json.load(f)

    assert MediaInfo.from_data(DATA) == MediaInfo(
        "<name>", 2000, "<imdbid>", None, None
    )


@pytest.mark.skip(reason="This isn't any different than `MediaInfo`")
def test_MovieInfo():
    pass


@pytest.mark.skip(reason="This isn't any different than `MediaInfo`")
def test_TvSeriesInfo():
    pass


def test_EpisodeInfo():
    with (INFO_DIR / "episode_info.json").open() as f:
        DATA = json.load(f)

    tv_series = TvSeriesInfo.from_data(DATA)
    tv_series.set_filepath("/path/to/file.mkv")

    episode_info = EpisodeInfo.from_data(DATA)
    episode_info.set_filepath("/path/to/file.mkv")

    assert episode_info == EPISODE_INFO1
    assert EpisodeInfo.from_tv_series(tv_series, 4, 3) == EPISODE_INFO1


def test_SubtitlesInfo():
    with (INFO_DIR / "subtitles_info.json").open() as f:
        DATA = json.load(f)

    assert SubtitlesInfo.from_data(DATA) == SUBTITLES_INFO1


def test_SearchResult():
    with (SAMPLES_DIR / "search_subtitles.json").open() as f:
        SAMPLE_RESP = json.load(f)["data"][0]

    search_result = SearchResult.from_data(SAMPLE_RESP)
    search_result.media.set_filepath("/path/to/file.mkv")
    assert SEARCH_RESULT2 == search_result
