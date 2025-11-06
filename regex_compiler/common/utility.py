from typing import Optional, TypeVar

T = TypeVar("T")


def unwrap(val: Optional[T]) -> T:
    """Unwrap an Optional value, raising an error if it is None."""
    if val is None:
        raise ValueError("Unexpected None in unwrap()")
    return val
