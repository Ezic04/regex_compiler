from typing import Optional, TypeVar

T = TypeVar("T")


def unwrap(val: Optional[T]) -> T:
    if val is None:
        raise ValueError("Unexpected None in unwrap()")
    return val
