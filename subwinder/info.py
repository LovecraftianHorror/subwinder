from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union, cast

from subwinder._constants import REPO_URL, TIME_FORMAT
from subwinder._internal_utils import CompatPath
from subwinder.exceptions import SubLibError
from subwinder.lang import LangFormat, lang_3s


@dataclass
class MediaInfo:
    """
    Data container for a generic Media.
    """

    name: str
    year: int
    imdbid: str
    _dirname: Optional[Path]
    _filename: Optional[Path]

    def __init__(
        self,
        name: str,
        year: int,
        imdbid: str,
        dirname: Optional[CompatPath],
        filename: Optional[CompatPath],
    ) -> None:
        self.name = name
        self.year = year
        self.imdbid = imdbid
        self.set_dirname(dirname)
        self.set_filename(filename)

    @classmethod
    def from_data(cls, data: dict) -> MediaInfo:
        name = data["MovieName"]
        # Sometimes this is returned as an `int`, sometimes it's a `str` ¯\_(ツ)_/¯
        year = int(data["MovieYear"])
        # For some reason opensubtitles sometimes returns this as an integer
        # Example: best guess when using `guess_media` for "the expanse" has
        #          `type(data["IDMovieIMDB"]) == int`
        imdbid = str(data.get("IDMovieImdb") or data["IDMovieIMDB"])

        return cls(name, year, imdbid, dirname=None, filename=None)

    def set_filepath(self, filepath: Optional[CompatPath]) -> None:
        if filepath is None:
            self.set_dirname(None)
            self.set_filename(None)
        else:
            filepath = Path(filepath)

            self.set_dirname(filepath.parent)
            self.set_filename(filepath.name)

    def set_filename(self, filename: Optional[CompatPath]) -> None:
        self._filename: Optional[Path] = None if filename is None else Path(filename)

    def set_dirname(self, dirname: Optional[CompatPath]) -> None:
        self._dirname = None if dirname is None else Path(dirname)

    def get_filepath(self) -> Optional[Path]:
        if self.get_filename() is None or self.get_dirname() is None:
            return None

        return cast(Path, self.get_dirname()) / cast(Path, self.get_filename())

    def get_filename(self) -> Optional[Path]:
        return self._filename

    def get_dirname(self) -> Optional[Path]:
        return self._dirname


class MovieInfo(MediaInfo):
    """
    Data container for a Movie.
    """

    # TODO: figure out if there is a way to do this without redefining
    @classmethod
    def from_data(cls, data: dict) -> MovieInfo:
        return cast(MovieInfo, super().from_data(data))


class TvSeriesInfo(MediaInfo):
    """
    Data container for a TV Series.
    """

    # TODO: figure out if there is a way to do this without redefining
    @classmethod
    def from_data(cls, data: dict) -> TvSeriesInfo:
        return cast(TvSeriesInfo, super().from_data(data))


@dataclass
class EpisodeInfo(TvSeriesInfo):
    """
    Data contianer for a single TV Series Episode.
    """

    season: int
    episode: int

    def __init__(
        self,
        name: str,
        year: int,
        imdbid: str,
        dirname: Optional[CompatPath],
        filename: Optional[CompatPath],
        season: int,
        episode: int,
    ) -> None:
        super().__init__(name, year, imdbid, dirname, filename)
        self.season = season
        self.episode = episode

    @classmethod
    def from_data(cls, data: dict) -> EpisodeInfo:
        tv_series = TvSeriesInfo.from_data(data)
        # Yay different keys for the same data!
        season = int(data.get("SeriesSeason") or data["Season"])
        episode = int(data.get("SeriesEpisode") or data["Episode"])

        return cls.from_tv_series(tv_series, season, episode)

    @classmethod
    def from_tv_series(
        cls, tv_series: TvSeriesInfo, season: int, episode: int
    ) -> EpisodeInfo:
        return cls(
            name=tv_series.name,
            year=tv_series.year,
            imdbid=tv_series.imdbid,
            dirname=tv_series.get_dirname(),
            filename=tv_series.get_filename(),
            season=season,
            episode=episode,
        )


BuiltMedia = Union[MovieInfo, EpisodeInfo, TvSeriesInfo]


# Build the right info object from the "MovieKind"
def build_media_info(data: dict) -> BuiltMedia:
    """
    Automatically builds `data` into the correct `MediaInfo` class. `dirname` and
    `filename` can be set to tie the resulting object to some local file.
    """
    MEDIA_MAP = {
        "movie": MovieInfo,
        "episode": EpisodeInfo,
        "tv series": TvSeriesInfo,
    }

    kind = data["MovieKind"]
    if kind in MEDIA_MAP:
        media_kind = cast(BuiltMedia, MEDIA_MAP[kind])
        return media_kind.from_data(data)

    raise SubLibError(
        f'The library encounterd an undefined MovieKind: "{kind}". You can raise an'
        f" issue at the library repo to address this {REPO_URL}"
    )


@dataclass
class UserInfo:
    """
    Data container holding basic user information.
    """

    id: str
    name: str

    @classmethod
    def from_data(cls, data: dict) -> Optional[UserInfo]:
        # Different keys for the same data again :/
        id = data.get("UserID") or data["IDUser"]

        # Special case of no user (like anonymously uploaded subtitles)
        if id == "0":
            return None

        return cls(id=id, name=data["UserNickName"])


@dataclass
class FullUserInfo(UserInfo):
    """
    Data container holding extensive user information.
    """

    rank: str
    num_uploads: int
    num_downloads: int
    preferred_languages: List[str]
    web_language: str

    @classmethod
    def from_data(cls, data: dict) -> FullUserInfo:
        user = cast(UserInfo, UserInfo.from_data(data))
        preferred = []
        for lang in data["UserPreferedLanguages"].split(","):
            # Ignore empty string in case of no preferred languages
            if lang:
                preferred.append(lang_3s.convert(lang, LangFormat.LANG_2))

        return cls(
            id=user.id,
            name=user.name,
            rank=data["UserRank"],
            num_uploads=int(data["UploadCnt"]),
            num_downloads=int(data["DownloadCnt"]),
            preferred_languages=preferred,
            web_language=data["UserWebLanguage"],
        )


@dataclass
class Comment:
    """
    Data container for a comment.
    """

    author: UserInfo
    date: datetime
    text: str

    @classmethod
    def from_data(cls, data: dict) -> Comment:
        author = cast(UserInfo, UserInfo.from_data(data))
        date = datetime.strptime(data["Created"], TIME_FORMAT)
        text = data["Comment"]

        return cls(author, date, text)


# TODO: are "global_24h_download_limit" and "client_24h_download_limit" ever different?
@dataclass
class DownloadInfo:
    """
    Data container for a user's daily download information.
    """

    ip: str
    downloaded: int
    remaining: int
    limit: int
    limit_checked_by: str

    @classmethod
    def from_data(cls, data: dict) -> DownloadInfo:
        limits = data["download_limits"]
        return cls(
            ip=limits["client_ip"],
            downloaded=int(limits["client_24h_download_count"]),
            remaining=int(limits["client_download_quota"]),
            limit=int(limits["client_24h_download_limit"]),
            limit_checked_by=limits["limit_check_by"],
        )


@dataclass
class ServerInfo:
    """
    Data container for various information for opensubtitles' server.
    """

    application: str
    users_online: int
    users_logged_in: int
    users_online_peak: int
    users_registered: int
    bots_online: int
    total_subtitles_downloaded: int
    total_subtitle_files: int
    total_movies: int
    daily_download_info: DownloadInfo

    @classmethod
    def from_data(cls, data: dict) -> ServerInfo:
        return cls(
            application=data["application"],
            users_online=int(data["users_online_total"]),
            users_logged_in=int(data["users_loggedin"]),
            users_online_peak=int(data["users_max_alltime"]),
            users_registered=int(data["users_registered"]),
            bots_online=int(data["users_online_program"]),
            total_subtitles_downloaded=int(data["subs_downloads"]),
            total_subtitle_files=int(data["subs_subtitle_files"]),
            total_movies=int(data["movies_total"]),
            daily_download_info=DownloadInfo.from_data(data),
        )


@dataclass
class SubtitlesInfo:
    """
    Data container for a set of uploaded Subtitles.
    """

    size: int
    id: str
    file_id: str
    sub_to_movie_id: Optional[str]
    filename: Path
    lang_2: str
    lang_3: str
    ext: str
    encoding: str

    @classmethod
    def from_data(cls, data: dict) -> SubtitlesInfo:
        # If the search was done with anything other than movie hash and size then
        # there isn't a "IDSubMovieFile"
        if data["IDSubMovieFile"] == "0":
            sub_to_movie_id = None
        else:
            sub_to_movie_id = data["IDSubMovieFile"]

        return cls(
            size=int(data["SubSize"]),
            id=data["IDSubtitle"],
            file_id=data["IDSubtitleFile"],
            sub_to_movie_id=sub_to_movie_id,
            filename=Path(data["SubFileName"]),
            lang_2=data["ISO639"],
            lang_3=data["SubLanguageID"],
            ext=data["SubFormat"].lower(),
            encoding=data["SubEncoding"],
        )


@dataclass
class SearchResult:
    """
    Data container for a search result from searching for subtitles.
    """

    author: Optional[UserInfo]
    media: MediaInfo
    subtitles: SubtitlesInfo
    upload_date: datetime
    num_bad_reports: int
    num_downloads: int
    num_comments: int
    rating: Optional[float]
    score: float

    @classmethod
    def from_data(cls, data: dict) -> SearchResult:
        return cls(
            author=UserInfo.from_data(data),
            media=build_media_info(data),
            subtitles=SubtitlesInfo.from_data(data),
            upload_date=datetime.strptime(data["SubAddDate"], TIME_FORMAT),
            num_bad_reports=int(data["SubBad"]),
            num_downloads=int(data["SubDownloadsCnt"]),
            num_comments=int(data["SubComments"]),
            # 0.0 is the listed rating if there are no ratings yet which seems deceptive
            # at a glance
            rating=None if data["SubRating"] == "0.0" else float(data["SubRating"]),
            score=data["Score"],
        )


@dataclass
class GuessMediaResult:
    """
    Data container for a result from `AuthSubwinder`'s `guess_media` method
    """

    best_guess: Optional[BuiltMedia]
    from_string: Optional[BuiltMedia]
    from_imdb: List[MediaInfo]

    @classmethod
    def from_data(cls, data: dict) -> GuessMediaResult:
        BEST_GUESS_KEY = "BestGuess"
        FROM_STRING_KEY = "GuessMovieFromString"
        IMDB_KEY = "GetIMDBSuggest"

        # Deal with missing entries by filling with empty values
        for key in [BEST_GUESS_KEY, FROM_STRING_KEY, IMDB_KEY]:
            if key not in data:
                data[key] = {}

        # So just in case you're wondering why there's all these hoops to jump
        # through. The API returns each value paired in a dict where the IMDB id is
        # the key, but since we don't know the key we have to do some extra work to
        # ignore it while still getting the value attached to it (Oh yeah, but
        # "BestGuess" is **not** returned this way, yet all the others are)
        best_guess = data[BEST_GUESS_KEY]

        # So this one is a bit complicated, from what I've seen sometimes this is a
        # `dict` where the key is the IMDB id, and sometimes its a `list` with length 1
        from_string = data[FROM_STRING_KEY]
        if type(from_string) == dict:
            from_string = list(from_string.values())

        if len(from_string) > 0:
            from_string = from_string[0]

        # When theres no results it's an empty `list`, when there are results it's a
        # `dict` so need to force the potentially empty `list` to a `dict` first
        from_imdb = list(dict(data[IMDB_KEY]).values())

        return cls(
            # Now that it's orgainzed build the appropriate `MediaInfo`
            best_guess=build_media_info(best_guess) if best_guess else None,
            from_string=build_media_info(from_string) if from_string else None,
            from_imdb=[build_media_info(m) for m in from_imdb],
        )
