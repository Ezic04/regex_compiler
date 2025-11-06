from enum import Enum, auto
from typing import Tuple, Iterator
from ..common.token import Token
from ..common.lexer_utils import LexerError, generic_lexer, scan_quoted_ident, is_not_eps


class RegexTokenType(Enum):
    """Token types for regex parsing."""
    LPAREN = auto()
    RPAREN = auto()
    STAR = auto()
    OR = auto()
    IDENT = auto()
    EOF = auto()


RegexToken = Token[RegexTokenType]
"""A token specialized for regex parsing."""


def regex_next_token(src: str, i: int) -> Tuple[RegexToken, int]:
    """Get the next token from the source string starting at index i."""
    match c := src[i]:
        case '(':
            return Token(RegexTokenType.LPAREN), i+1
        case ')':
            return Token(RegexTokenType.RPAREN), i+1
        case '*':
            return Token(RegexTokenType.STAR), i+1
        case '|':
            return Token(RegexTokenType.OR), i+1
        case '\'':
            ident_str, i = scan_quoted_ident(src, i)
            is_not_eps(ident_str)
            return Token(RegexTokenType.IDENT, ident_str), i + 1
        case _ if c.isalnum():
            return Token(RegexTokenType.IDENT, c), i + 1
        case _:
            raise LexerError(f"Unexpected character {c!r} at position {i}")


def lex_regex(src: str) -> Iterator[RegexToken]:
    """Lex the source string into regex tokens."""
    return generic_lexer(src, regex_next_token, RegexTokenType)
