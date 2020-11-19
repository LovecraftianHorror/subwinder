from datetime import datetime as dt
from pathlib import Path

from subwinder.info import (
    DownloadInfo,
    EpisodeInfo,
    FullUserInfo,
    GuessMediaResult,
    MovieInfo,
    SearchResult,
    ServerInfo,
    SubtitlesInfo,
    UserInfo,
)
from subwinder.media import Media

TEST_DIR = Path(__file__).resolve().parent
REPO_DIR = TEST_DIR.parent
SAMPLES_DIR = TEST_DIR / "sample_responses"
INFO_DIR = TEST_DIR / "sample_info"

MEDIA1 = Media.from_parts("18379ac9af039390", 366876694, "/path/to", "file.mkv")
USER_INFO1 = UserInfo("1332962", "elderman")

FULL_USER_INFO1 = FullUserInfo(
    id="6",
    name="os",
    rank="super admin",
    num_uploads=296,
    num_downloads=1215,
    preferred_languages=["de", "en", "fr"],
    web_language="en",
)

MOVIE_INFO1 = MovieInfo(
    name="<movie-name>",
    year=2015,
    imdbid="<imdbid>",
    dirname="movie_dir",
    filename="movie_file",
)

EPISODE_INFO1 = EpisodeInfo(
    name='"Fringe" Alone in the World',
    year=2011,
    imdbid="1998676",
    dirname="/path/to",
    filename="file.mkv",
    season=4,
    episode=3,
)

SUBTITLES_INFO1 = SubtitlesInfo(
    size=71575,
    id="3387112",
    file_id="<file-id>",
    sub_to_movie_id=None,
    filename="sub-filename.sub-ext",
    lang_2="de",
    ext="<ext>",
    encoding="UTF-8",
)

SUBTITLES_INFO2 = SubtitlesInfo(
    size=58024,
    id="4251071",
    file_id="1952941557",
    sub_to_movie_id="3585468",
    filename="Fringe.S04E03.HDTV.XviD-LOL.srt",
    lang_2="en",
    ext="srt",
    encoding="UTF-8",
)

SEARCH_RESULT1 = SearchResult(
    author=None,
    media=MOVIE_INFO1,
    subtitles=SUBTITLES_INFO1,
    upload_date=dt(2015, 3, 29, 13, 23, 44),
    num_bad_reports=1,
    num_downloads=22322,
    num_comments=0,
    rating=None,
    score=105.0,
)

SEARCH_RESULT2 = SearchResult(
    USER_INFO1,
    EPISODE_INFO1,
    SUBTITLES_INFO2,
    dt(2011, 10, 8, 7, 36, 1),
    num_bad_reports=0,
    num_downloads=57765,
    num_comments=2,
    rating=None,
    score=103.57765,
)

DOWNLOAD_INFO = DownloadInfo(
    ip="1.1.1.1",
    downloaded=0,
    remaining=200,
    limit=200,
    limit_checked_by="user_ip",
)

SERVER_INFO = ServerInfo(
    application="OpenSuber v0.2",
    users_online=5117,
    users_logged_in=55,
    users_online_peak=27449,
    users_registered=1025195,
    bots_online=3685,
    total_subtitles_downloaded=765919208,
    total_subtitle_files=1864277,
    total_movies=136445,
    daily_download_info=DOWNLOAD_INFO,
)

GUESS_MEDIA_RESULT = GuessMediaResult(
    best_guess=MOVIE_INFO1,
    from_string=EPISODE_INFO1,
    from_imdb=[],
)
