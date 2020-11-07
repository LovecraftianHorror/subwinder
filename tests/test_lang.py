from datetime import timedelta
from typing import Any
from unittest.mock import call, patch

from subwinder.lang import (
    LangFormat,
    _converter,
    _LangConverter,
    lang_2s,
    lang_3s,
    lang_longs,
)

# TODO: add a test for getting the lang list from the api response, mocking out request

# Snippet of the GetSubLanguages response
RESP = [
    {"ISO639": "de", "SubLanguageID": "ger", "LanguageName": "German"},
    {"ISO639": "en", "SubLanguageID": "eng", "LanguageName": "English"},
    {"ISO639": "fr", "SubLanguageID": "fre", "LanguageName": "French"},
]


def test_LangConverter() -> None:
    converter = _LangConverter()

    with patch.object(converter, "_fetch", return_value=RESP) as mocked:
        # After first update converter shouldn't request again for an hour
        converter._maybe_update()

        # These will not call `_get_languages`
        converter._maybe_update()
        assert "eng" == converter.convert("en", LangFormat.LANG_2, LangFormat.LANG_3)
        assert "English" == converter.convert(
            "eng", LangFormat.LANG_3, LangFormat.LANG_LONG
        )
        assert ["de", "en", "fr"] == converter.list(LangFormat.LANG_2)
        assert ["ger", "eng", "fre"] == converter.list(LangFormat.LANG_3)
        assert ["German", "English", "French"] == converter.list(LangFormat.LANG_LONG)

        # `_get_languages` should only be called once
        mocked.assert_called_once_with()

        # Now wait long enough that we will refresh the langs
        converter._last_updated -= timedelta(seconds=3600)  # type: ignore
        converter.list(LangFormat.LANG_2)
        mocked.assert_has_calls([call(), call()])


def test_globals(no_fake_langs: Any) -> None:
    with patch.object(_converter, "_fetch", return_value=RESP) as mocked:
        # Check all the conversions
        assert "eng" == lang_2s.convert("en", LangFormat.LANG_3)
        assert "English" == lang_3s.convert("eng", LangFormat.LANG_LONG)
        assert "en" == lang_longs.convert("English", LangFormat.LANG_2)

        # Check all the listings
        assert ["de", "en", "fr"] == list(lang_2s)
        assert ["ger", "eng", "fre"] == list(lang_3s)
        assert ["German", "English", "French"] == list(lang_longs)

        # Check `__contains__`
        assert "de" in lang_2s
        assert "eng" in lang_3s
        assert "French" in lang_longs

        # `_get_languages` should only be called once
        mocked.assert_called_once_with()
