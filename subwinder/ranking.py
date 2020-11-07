from typing import List, Optional

from subwinder.info import GuessMediaResult, SearchResult
from subwinder.types import BuiltMedia


def rank_guess_media(results: GuessMediaResult, query: int) -> Optional[BuiltMedia]:
    """
    The default ranking function used to determine the best result for `AuthSubwinder`'s
    `.guess_media(...)` method. `results` is the information returned as specified by
    trac.opensubtitles.org/projects/opensubtitles/wiki/XMLRPC#GuessMovieFromString
    and `query` is the original `str` being guessed.
    """
    return results.best_guess


def rank_search_subtitles(
    results: List[SearchResult],
    query: int,
    exclude_bad: bool = True,
    sub_exts: Optional[List[str]] = None,
) -> Optional[SearchResult]:
    """
    The default ranking function used to determine the best result for `AuthSubwinder`'s
    `.search_subtitles(...)` method. `results` is the information returned as specified
    by https://trac.opensubtitles.org/projects/opensubtitles/wiki/XMLRPC#SearchSubtitles
    `query` is the object passed in to search for. `exclude_bad` just skips any result
    that has been marked as bad by a user, and `sub_exts` is an optional
    case-insensitive list of accepted subtitle extensions.
    """
    best_result = None
    max_score = None

    # Force list of `sub_exts` to be lowercase
    sub_exts = None if sub_exts is None else [ext.lower() for ext in sub_exts]

    for result in results:
        # Skip if someone listed sub as bad and `exclude_bad` is `True`
        if exclude_bad and result.num_bad_reports > 0:
            continue

        # Skip incorrect `sub_ext`s if provided
        if sub_exts is not None and result.subtitles.ext.lower() not in sub_exts:
            continue

        # Pick the one with the highest score if it matches all other criteria
        if max_score is None or result.score > max_score:
            best_result = result
            max_score = result.score

    return best_result
