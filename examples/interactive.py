#!/usr/bin/env python
import sys
from datetime import datetime as dt
from typing import Union, cast

# TODO: waiting to stabilize still
from subwinder import AuthSubwinder, _types, info


def main() -> None:
    # Language of our desired subtitles
    LANG = "en"
    interative(LANG)


def interative(lang: str) -> None:
    # Assumes all the credentials are set using environment variables
    with AuthSubwinder() as asw:
        # Give a nice friendly prompt
        user_info = asw.user_info()
        download_info = asw.daily_download_info()
        print(
            f"Hello {user_info.name}, you have {download_info.remaining} of"
            f" {download_info.limit} downloads remaining for the day!\n"
        )

        # Search for some media
        query = input("What media do you want to find subtitles for? ")
        media = asw.suggest_media(query)

        # Build our extended objects and display the media
        ext_media = [build_extended_mediainfo(m) for m in media]
        for i, m in enumerate(ext_media):
            print(f"{i}) {m}")
        print()

        # Find which one they want to view
        resp = int(input(f"Which do you want to see? (0 -> {len(ext_media) - 1}) "))
        if resp < 0 or resp >= len(ext_media):
            sys.exit(f"Entry {resp} out of bounds (0 -> {len(ext_media) - 1})")

        # Search for the subtitles
        desired: _types.BuiltMedia = ext_media[resp]

        # This is the special case of a `TvSeriesInfo` again. So if we have a
        # `TvSeriesInfo` we need to get the specific episode to search for. If you have
        # information about the number of series and episodes available then you could
        # search for all of them at once too
        if type(desired) == ExtTvSeriesInfo:
            print("It looks like you selected a tv series!")
            season = int(input("What season do you want? "))
            episode = int(input("What episode do you want? "))
            print()
            desired = info.EpisodeInfo.from_tv_series(
                cast(ExtTvSeriesInfo, desired), season, episode
            )
        to_download: _types.SearchQueryable = desired
        results = asw.search_subtitles_unranked([(to_download, lang)])[0]
        ext_results = [ExtSearchResult(result) for result in results]

        print("Results:")
        for i, ext_result in enumerate(ext_results):
            print(f"{i}) {ext_result}")
        print()

        preview_index = int(
            input(f"Which one do you want to preview? (0 -> {len(ext_results) - 1}) ")
        )
        if preview_index < 0 or preview_index >= len(ext_results):
            sys.exit(f"Entry {resp} out of bounds (0 -> {len(ext_results) - 1})")
        result = ext_results[preview_index]
        preview = asw.preview_subtitles([result])[0]
        # Limit preview size
        print(f"Preview:\n{preview[:200]}\n")

        y_or_n = (
            input("Do you want to download these subtitles? (Y/n) ").strip().lower()
        )
        if y_or_n == "n":
            sys.exit()
        elif y_or_n not in ["y", ""]:
            sys.exit(f"Unrecognized option '{resp}'")

        location = input("Where do you want them downloaded? ")

        download_path = asw.download_subtitles([result], download_dir=location)[0]
        print(f"Downloaded to '{download_path}', have a nice day!")


# And now we can extend all the `MediaInfo` classes we care about
class ExtMovieInfo(info.MovieInfo):
    def __init__(self, movie: info.MovieInfo) -> None:
        super().__init__(**movie.__dict__)

    def __str__(self) -> str:
        return f"(Movie)\t{self.name}\t({self.year})\t(imdb: {self.imdbid})"


class ExtTvSeriesInfo(info.TvSeriesInfo):
    def __init__(self, tv_series: info.TvSeriesInfo) -> None:
        super().__init__(**tv_series.__dict__)

    def __str__(self) -> str:
        return f"(TV Series)\t{self.name}\t({self.year})\t(imdb: {self.imdbid})"


# Helper function to make it easier to build the appropriate extended `MediaInfo`
def build_extended_mediainfo(obj) -> Union[ExtMovieInfo, ExtTvSeriesInfo]:
    CLASS_MAP = {
        info.MovieInfo: ExtMovieInfo,
        info.TvSeriesInfo: ExtTvSeriesInfo,
    }

    # Use the correct extended class for `obj`
    class_type = CLASS_MAP[type(obj)]
    return class_type(obj)


class ExtSearchResult(info.SearchResult):
    def __init__(self, search_result: info.SearchResult) -> None:
        # All of the members are named the same the params so we can just pass in
        super().__init__(**search_result.__dict__)

    def __str__(self) -> str:
        TIME_FMT = "%Y-%m-%d %H:%M:%S"
        upload = dt.strftime(self.upload_date, TIME_FMT)
        sub = self.subtitles
        author = "NA" if self.author is None else self.author.name
        return f"[{upload} | by {author} | {sub.ext}] {sub.filename}"


if __name__ == "__main__":
    main()
