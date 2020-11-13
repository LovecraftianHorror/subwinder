from typing import Callable, Optional, Tuple, Union

from subwinder.info import (  # noqa: F401 Handle rexports better before public
    BuiltMedia,
    EpisodeBase,
    EpisodeInfo,
    MovieBase,
    MovieInfo,
    SearchResult,
    SubtitlesInfo,
    TvSeriesBase,
)
from subwinder.media import Media

# TODO: these two should be able to specify 2 specific args and then any others, but it
#       was giving me problems
RankGuessMedia = Callable[..., Optional[BuiltMedia]]
RankSearchSubtitles = Callable[..., Optional[SearchResult]]
SearchQueryable = Union[Media, MovieBase, EpisodeBase]
SearchQuery = Tuple[SearchQueryable, str]
SubContainer = Union[SearchResult, SubtitlesInfo]
