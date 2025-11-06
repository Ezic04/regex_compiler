from typing import Generic, Iterator, Optional, TypeVar, Set
from .token import Token, TokenTypeT, SetToken, SetTokenType


class ParserError(Exception):
    pass


T = TypeVar("T")


class Peekable(Iterator[T], Generic[T]):  # AI gen
    """An iterator that supports peeking at the next element without consuming it."""

    def __init__(self, it: Iterator[T]) -> None:
        self._it = it
        self._peeked: Optional[T] = None

    def __next__(self) -> T:
        if self._peeked is not None:
            value = self._peeked
            self._peeked = None
            return value
        return next(self._it)

    def peek(self) -> T:
        if self._peeked is None:
            self._peeked = next(self._it)
        return self._peeked

    def next(self) -> T:
        return self.__next__()


def expect(tokens: Peekable[Token[TokenTypeT]], expected_type: TokenTypeT) -> Token[TokenTypeT]:  # AI gen
    """Expect the next token to be of the given type, otherwise raise ParserError."""
    token = tokens.next()
    if token.type != expected_type:
        raise ParserError(
            f"Expected token {expected_type.name}, got {token!r}"
        )
    return token


def expect_value(tokens: Peekable[Token[TokenTypeT]], ttype: TokenTypeT) -> str:  # AI gen
    """Expect the next token to be of the given type and return its value, otherwise raise ParserError."""
    token = expect(tokens, ttype)
    if token.value is None:
        raise ParserError(f"Token {ttype.name} has no value")
    return token.value


def parse_set(tokens: Iterator[SetToken]) -> Set[str]:
    """Parse a set literal from tokens and return the set of identifiers."""
    tokens = Peekable(tokens)
    ret: Set[str] = set()
    expect(tokens, SetTokenType.LBRACE)
    ret.add(expect_value(tokens, SetTokenType.IDENT))
    while tokens.peek().type == SetTokenType.COMMA:
        tokens.next()
        ret.add(expect_value(tokens, SetTokenType.IDENT))
    expect(tokens, SetTokenType.RBRACE)
    expect(tokens, SetTokenType.EOF)
    return ret
