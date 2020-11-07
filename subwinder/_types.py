from typing import Callable, Optional, Tuple, Union

from subwinder.info import (
    BuiltMedia,
    EpisodeInfo,
    MovieInfo,
    SearchResult,
    SubtitlesInfo,
)
from subwinder.media import Media

# TODO: these two should be able to specify 2 specific args and then any others, but it
#       was giving me problems
RankGuessMedia = Callable[..., Optional[BuiltMedia]]
RankSearchSubtitles = Callable[..., Optional[SearchResult]]
SearchQuery = Tuple[Union[Media, MovieInfo, EpisodeInfo], str]
SubContainer = Union[SearchResult, SubtitlesInfo]
