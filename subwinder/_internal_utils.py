from pathlib import Path
from typing import Any, Tuple, Union

PathLike = Union[str, Path]


def type_check(
    obj: Any, valid_classes: Union[type, Tuple[Union[type, Tuple[Any, ...]], ...]]
) -> None:
    if not isinstance(obj, valid_classes):
        raise ValueError(
            f"Expected `obj` to be type from {valid_classes}, but got type {type(obj)}"
            " instead"
        )
