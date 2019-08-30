from datetime import datetime

from subwinder.constants import _TIME_FORMAT


class Comment:
    def __init__(self, data):
        self.author = UserInfo(data["UserID"], data["UserNickName"])
        self.created = datetime.strptime(data["Created"], _TIME_FORMAT)
        self.comment_str = data["comment"]


class UserInfo:
    def __init__(self, id, nickname):
        self.id = id
        self.nickname = nickname


class FullUserInfo(UserInfo):
    def __init__(self, data):
        super().__init__(data["IDUser"], data["UserNickName"])
        self.rank = data["UserRank"]
        self.uploads = int(data["UploadCnt"])
        self.downloads = int(data["DownloadCnt"])
        # FIXME: this is in lang_3 instead of lang_2, convert
        self.prefered_languages = data["UserPreferedLanguages"].split(",")
        self.web_language = data["UserWebLanguage"]


class MovieInfo:
    def __init__(self, data):
        self.name = data["MovieName"]
        self.year = int(data["MovieYear"])
        self.imdbid = data.get("IDMovieImdb") or data.get("IDMovieIMDB")


class EpisodeInfo(MovieInfo):
    def __init__(self, data):
        super().__init__(data)
        # Yay different keys for the same data!
        season = data.get("SeriesSeason") or data.get("Season")
        episode = data.get("SeriesEpisode") or data.get("Episode")
        self.season_num = int(season)
        self.episode_num = int(episode)


class SubtitlesInfo:
    def __init__(self, data):
        self.size = int(data["SubSize"])
        self.downloads = int(data["SubDownloadsCnt"])
        self.num_comments = int(data["SubComments"])

        self.rating = float(data["SubRating"])

        self.id = data["IDSubtitle"]
        self.file_id = data["IDSubtitleFile"]
        self.lang_2 = data["ISO639"]
        self.ext = data["SubFormat"]
        self.encoding = data["SubEncoding"]