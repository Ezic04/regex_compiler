from typing import TypeVar, Generic, Optional
from dataclasses import dataclass
from enum import Enum, auto

TokenTypeT = TypeVar("TokenTypeT", bound=Enum)


@dataclass(frozen=True, slots=True)
class Token(Generic[TokenTypeT]):
    type: TokenTypeT
    value: Optional[str] = None

    @classmethod
    def eof(cls, token_type: TokenTypeT) -> "Token[TokenTypeT]":
        return cls(token_type)

    def __repr__(self) -> str:
        if self.value is None:
            return self.type.name
        return f"{self.type.name}({self.value!r})"


class SetTokenType(Enum):
    LBRACE = auto()
    RBRACE = auto()
    COMMA = auto()
    IDENT = auto()
    EOF = auto()


SetToken = Token[SetTokenType]
