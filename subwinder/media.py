from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, cast

from subwinder._internal_utils import CompatPath
from subwinder.utils import special_hash


@dataclass
class Media:
    """
    Data container representing some media (Movie, Episode, etc.) to search for.
    """

    hash: str
    size: int
    _dirname: Optional[Path]
    _filename: Optional[Path]

    def __init__(self, filepath: CompatPath) -> None:
        """
        Builds a `Media` object from a local file.
        """
        filepath = Path(filepath)
        hash = special_hash(filepath)
        size = filepath.stat().st_size

        self._from_parts(hash, size)
        # Set file info from given `filepath`
        self.set_filepath(filepath)

    @classmethod
    def from_parts(
        cls,
        hash: str,
        size: int,
        dirname: Optional[CompatPath] = None,
        filename: Optional[CompatPath] = None,
    ) -> Media:
        """
        Builds a `Media` object from the individual parts.
        """
        # Make a bare `Media` skipping the call to `__init__`
        media = cls.__new__(cls)
        media._from_parts(hash, size, dirname, filename)

        return media

    def _from_parts(
        self,
        hash: str,
        size: int,
        dirname: Optional[CompatPath] = None,
        filename: Optional[CompatPath] = None,
    ) -> Media:
        self.hash = hash
        self.size = size
        self.set_dirname(dirname)
        self.set_filename(filename)

        return self

    def set_filepath(self, filepath: Optional[CompatPath]) -> None:
        if filepath is None:
            self.set_filename(None)
            self.set_dirname(None)
        else:
            filepath = Path(filepath)

            self.set_filename(filepath.name)
            self.set_dirname(filepath.parent)

    def set_filename(self, filename: Optional[CompatPath]) -> None:
        self._filename = None if filename is None else Path(filename)

    def set_dirname(self, dirname: Optional[CompatPath]) -> None:
        self._dirname = None if dirname is None else Path(dirname)

    def get_filepath(self) -> Optional[Path]:
        if self.get_filename() is None or self.get_dirname() is None:
            return None

        return cast(Path, self.get_dirname()) / cast(Path, self.get_filename())

    def get_filename(self) -> Optional[Path]:
        return self._filename

    def get_dirname(self) -> Optional[Path]:
        return self._dirname
