"""
I just wanted the option to have some tests run by default, but I couldn't find anything
documented for it, so enjoy this pytest black magic.
"""

import logging
from datetime import datetime as dt

import pytest  # type: ignore

from subwinder.lang import _converter

NON_DEFAULT_MARKERS = ["io_heavy", "slow"]


def pytest_addoption(parser):
    # Add a command line option to run all tests
    parser.addoption(
        "--run-all",
        action="store_true",
        help="Run all tests (some are skipped by default because they're slow)",
    )


# XXX: Temporary workaround till mccabe has a new release
#      https://github.com/PyCQA/mccabe/pull/83
def pytest_configure(config):
    # Make flake8 less verbose
    logging.getLogger("flake8").setLevel(logging.CRITICAL)


@pytest.fixture(autouse=True)
def _skip_non_default(request):
    node = request.node

    # IF we are skipping non default and we have a mark
    if skip_non_default(request) and len(node.own_markers) > 0:
        for marker in node.own_markers:
            if marker.name in NON_DEFAULT_MARKERS:
                pytest.skip(
                    f"Skipping mark for reason: {node.own_markers[0].name}. Run with"
                    " option --run-all to run this"
                )


def skip_non_default(request):
    run_all = request.config.getoption("--run-all")
    mark = request.config.getoption("-m")

    # skip tests if mark value isn't given and run all is not specified
    return not mark and not run_all


@pytest.fixture(autouse=True)
def _fake_langs():
    stored = _converter.dump()
    _converter.set(
        dt.now(),
        [["de", "en", "fr"], ["ger", "eng", "fre"], ["German", "English", "French"]],
    )

    yield

    _converter.set(*stored)


# Negates `_fake_langs` which by default fakes the language listing
@pytest.fixture
def no_fake_langs():
    stored = _converter.dump()

    yield

    _converter.set(*stored)
