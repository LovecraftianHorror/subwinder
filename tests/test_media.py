from pathlib import Path

from subwinder import Media
from tests.utils import RandomTempFile


def test_Media() -> None:
    with RandomTempFile(128 * 1024, seed=1) as rand_file:
        media = Media(rand_file)

        assert media.hash == "25182dd38c3b3793"
        assert media.size == 128 * 1024
        assert media.get_filename() == Path(rand_file.name)
        assert media.get_dirname() == rand_file.parent
        assert media.get_filepath() == rand_file
