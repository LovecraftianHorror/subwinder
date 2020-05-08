#!/usr/bin/env python
from subwinder import AuthSubwinder, Media
from subwinder.exceptions import SubHashError
from subwinder import info
from subwinder.ranking import rank_search_subtitles

from datetime import datetime as dt
import json
from pathlib import Path


def main():
    # Setting up some of the constants for our program
    # Directory that we're scanning from and moving to
    INPUT_DIR = Path("/path/to/input/dir")
    OUTPUT_DIR = Path("/path/to/output/dir")
    # Whitelist used for our custom ranking function
    AUTHOR_WHITELIST = ["john", "jacob", "jingleheimer", "schmidt"]
    # Our preferred sub extensions
    SUB_EXTS = ["ssa", "ass", "srt"]
    # File that we're storing all our saved subtitles info in for later in case you
    # want to rebuild any of the results from it and comment/vote/report them
    SAVED_SUBS_FILE = Path("/path/to/ledger.json")
    # The language we want to search for
    LANG = "en"

    # So now let's get all the files in `INPUT_DIR` as `Media` objects
    print(f"Scanning {INPUT_DIR}... ", end="")
    queries = []
    for item in INPUT_DIR.iterdir():
        # We only care about files
        if item.is_file():
            # Hashing can fail if the file is too small (under 128 KiB)
            try:
                queries.append((Media(item), LANG))
            except SubHashError:
                pass
    print(f"Found {len(queries)} files")

    # And now onto using the API, so I'm going to assume that all the credentials are
    # set with `OPEN_SUBTITLES_USERNAME`, `OPEN_SUBTITLES_PASSWORD`, and
    # `OPEN_SUBTITLES_USERAGENT`, but you can pass them as params to `AuthSubwinder` too
    with AuthSubwinder() as asw:
        # Now we can search for all of our `media` using our custom ranking function
        print("Searching... ", end="")
        results = asw.search_subtitles(
            queries, custom_rank_func, AUTHOR_WHITELIST, SUB_EXTS,
        )
        # Filter out items that didn't get any matches
        results = [result for result in results if result is not None]
        print(f"Found {len(results)} matches")

        # Your number of downloads from the API are on a daily limit so slice our
        # desired number of downloads to the max
        results = results[: asw.daily_download_info().remaining]
        print(f"Downloading {len(results)} subtitles... ", end="")
        download_paths = asw.download_subtitles(
            results, name_format="{media_name}.{lang_3}.{ext}"
        )
        print("Downloaded")

        # Move all the media that we have subtitles for now
        # Note: that this does not retain any special directory structure from
        #       `INPUT_DIR` in `OUTPUT_DIR`
        print(f"Moving matched media and subtitle files to {OUTPUT_DIR}... ", end="")
        for result, download in zip(results, download_paths):
            from_media_path = result.media.dirname / result.media.filename
            to_media_path = OUTPUT_DIR / from_media_path.name
            from_media_path.rename(to_media_path)

            from_sub_path = download
            to_sub_path = OUTPUT_DIR / from_sub_path.name
            from_sub_path.rename(to_sub_path)
        print("Moved")

        # Save the search results to a file in case we want them later
        print(f"Updating index of saved files {SAVED_SUBS_FILE}... ", end="")
        if SAVED_SUBS_FILE.is_file():
            with SAVED_SUBS_FILE.open() as file:
                saved_subs = json.load(file)
        else:
            saved_subs = []

        ext_results = [ExtSearchResult.from_search_result(result) for result in results]
        saved_subs += [ext_result.to_json_dict() for ext_result in ext_results]

        with SAVED_SUBS_FILE.open("w") as file:
            json.dump(saved_subs, file)
        print("Updated")


# Lets setup our custom ranking function
# So the goal of this ranking function is to prefer uploads from a whitelist of authors
# and if no results are found from that whitelist fallback to the default ranking
# function, finally if no results are found by that either the just fallback to picking
# the first result found.
def custom_rank_func(results, query, author_whitelist, sub_exts=None):
    # No results :(
    if len(results) == 0:
        return None

    return (
        rank_by_whitelist(results, query, author_whitelist)
        # Fallback to default ranking, but we decide not to `exclude_bad`
        or rank_search_subtitles(results, query, exclude_bad=False, sub_exts=sub_exts)
        # Fallback to the first result
        or results[0]
    )


def rank_by_whitelist(results, query, author_whitelist):
    # Search all the results for a known-good author
    for result in results:
        for author in author_whitelist:
            if author == result["UserNickName"]:
                return result

    # No matching result
    return None


# So with the libraries API (due to the design of opensubtitles.org's API) there is no
# easy way to link a local subtitle file with a `SearchResult`. So if you want to do
# anything that would require that `SearchResult` later you likely want to serialize it
# to some form to store it. For this example we will just use JSON because it's easy.
# The nice thing is we can just inherit from `SearchResult` while still being able to
# pass in our extended class to things that would normally expect a `SearchResult`.
class ExtSearchResult(info.SearchResult):
    @classmethod
    def from_search_result(cls, search_result):
        # We just want all the members from `search_result` in our `ExtSearchResult`
        # Yes this seems hacky, python's classes are _interesting_, so were going to
        # create a ExtSearchResult skipping __init__ by using __new__ then set our
        # members (aka __dict__) to all of those from `search_result`
        ext_search_result = ExtSearchResult.__new__(ExtSearchResult)
        ext_search_result.__dict__ = search_result.__dict__
        return ext_search_result

    def to_json_dict(self):
        # Need to get everything into a `dict` of json serializable values
        json_dict = {
            "author": self.author.__dict__,
            "media": self.media.__dict__,
            # `self.media` can be one of several types inheriting from `info.MediaInfo`
            "media_type": self.media.__class__.__name__,
            "subtitles": self.subtitles.__dict__,
            "upload_date": dt.strftime(self.upload_date, "%Y-%m-%d %H:%M:%S"),
        }
        json_dict["media"]["dirname"] = str(self.media.dirname)
        json_dict["media"]["filename"] = str(self.media.filename)
        json_dict["subtitles"]["filename"] = str(self.subtitles.filename)

        return json_dict

    # TODO: setup up custom json decoder and encoder
    @classmethod
    def from_json_dict(cls, json_dict):
        # And now we just need to do the reverse of `.to_json_dict(...)` with some extra
        # song and dance (If you were really doing this it could make sense to extend
        # the other classes or set up an alternate constructor to make this easier)
        search_result = info.SearchResult.__new__(info.SearchResult)
        search_result.author = info.UserInfo.__new__(info.UserInfo)
        # Get the class back from the media type
        media_type = getattr(info, json_dict["media_type"])
        search_result.media = media_type.__new__(media_type)
        search_result.subtitles = info.SubtitlesInfo.__new__(info.SubtitlesInfo)

        search_result.author.__dict__ = json_dict["author"]
        search_result.media.__dict__ = json_dict["media"]
        search_result.media.dirname = Path(search_result.media.dirname)
        search_result.media.filename = Path(search_result.media.filename)
        search_result.subtitles.__dict__ = json_dict["subtitles"]
        search_result.subtitles.filename = Path(search_result.subtitles.filename)
        search_result.upload_date = dt.strptime(
            json_dict["upload_date"], "%Y-%m-%d %H:%M:%S"
        )

        # Now return the `ExtSearchResult` for our `SearchResult`
        return ExtSearchResult.from_search_result(search_result)


if __name__ == "__main__":
    main()