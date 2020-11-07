# Note: this whole file uses enough global variables to make my skin crawl, but I can't
# really think of a nicer way of exposing everything
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

# See: https://github.com/LovecraftianHorror/subwinder/issues/52#issuecomment-637333960
# if you want to know why `request` isn't imported with `from`
import subwinder._request
from subwinder._request import Endpoints
from subwinder.exceptions import SubLangError

# TODO: why isn't this an enum?
_LANG_2_KEY = "ISO639"
_LANG_3_KEY = "SubLanguageID"
_LANG_LONG_KEY = "LanguageName"


class LangFormat(Enum):
    LANG_2 = 0
    LANG_3 = 1
    LANG_LONG = 2


LastUpdated = Optional[datetime]
Langs = List[List[str]]


class _LangConverter:
    """
    This class is used as a common converter to cache the language response from the API
    and handle converting between the separate forms. Caching in this way limits
    unnecessary requests to the API along with setting up an easy way to convert between
    any of the forms.
    """

    _last_updated: LastUpdated
    _langs: Langs

    def __init__(self) -> None:
        self.default()

    def _fetch(self) -> List[Dict[str, str]]:
        return subwinder._request.request(Endpoints.GET_SUB_LANGUAGES, None)["data"]

    def _maybe_update(self, force: bool = False) -> None:
        # Language list should refresh every hour, return early if still fresh unless
        # update is `force`d
        if not force and self._last_updated is not None:
            if (datetime.now() - self._last_updated).total_seconds() < 3600:
                return

        # Get language list from api
        lang_sets = self._fetch()

        # Reset then recollect info
        self.default()
        for lang_set in lang_sets:
            self._langs[LangFormat.LANG_2.value].append(lang_set[_LANG_2_KEY])
            self._langs[LangFormat.LANG_3.value].append(lang_set[_LANG_3_KEY])
            self._langs[LangFormat.LANG_LONG.value].append(lang_set[_LANG_LONG_KEY])

        # Refresh updated time
        self._last_updated = datetime.now()

    def default(self) -> None:
        self.set(None, [[] for _ in list(LangFormat)])

    def dump(self) -> Tuple[LastUpdated, Langs]:
        last_updated = self._last_updated
        langs = self._langs

        self.default()

        return last_updated, langs

    def set(self, last_updated: LastUpdated, langs: Langs) -> None:
        self._last_updated = last_updated
        self._langs = langs

    def convert(self, lang: str, from_format: LangFormat, to_format: LangFormat) -> str:
        self._maybe_update()

        try:
            lang_index = self._langs[from_format.value].index(lang)
        except ValueError:
            raise SubLangError(
                f"Tried to convert language '{lang}', but not found in language list:"
                f" {self._langs[from_format.value]}"
            )

        return self._langs[to_format.value][lang_index]

    def list(self, lang_format: LangFormat) -> List[str]:
        self._maybe_update()

        return self._langs[lang_format.value]


# `_converter` shared by all the `_Lang`s
_converter = _LangConverter()


@dataclass
class _Lang(Iterable):
    """
    Class that represents all actions for one of the three lang formats returned by the
    API. each `_Lang` shares a common `_converter` to try and reduce API calls as much
    as possible. You should be using the global `lang_2s`, `lang_3s`, and `lang_longs`
    instead of building more of these (hence it being private).
    """

    _format: LangFormat

    def __iter__(self) -> Iterator[str]:
        return iter(_converter.list(self._format))

    def __len__(self) -> int:
        return len(_converter.list(self._format))

    def convert(self, lang: str, to_format: LangFormat) -> str:
        """
        Convert the `lang` from the current format to `to_format`.
        """
        return _converter.convert(lang, self._format, to_format)


lang_2s = _Lang(LangFormat.LANG_2)
lang_3s = _Lang(LangFormat.LANG_3)
lang_longs = _Lang(LangFormat.LANG_LONG)
