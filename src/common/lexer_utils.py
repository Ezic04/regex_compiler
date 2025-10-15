from typing import Iterator, Callable, Type, Tuple
from .token import Token, TokenTypeT, SetToken, SetTokenType


class LexerError(Exception):
    pass


def generic_lexer(
    src: str,
    next_token_func: Callable[[str, int], tuple[Token[TokenTypeT], int]],
    token_type_cls: Type[TokenTypeT]
) -> Iterator[Token[TokenTypeT]]:
    """A generic lexer that uses the provided next_token_func to tokenize the input string."""
    i = 0
    while i < len(src):
        c = src[i]
        if c.isspace():
            i += 1
            continue
        token, new_i = next_token_func(src, i)
        yield token
        i = new_i
    yield Token.eof(token_type_cls.EOF)  # type: ignore


def is_valid_ident_char(c: str) -> bool:
    return c.isalnum() or c == '_' or c == '-'


def scan_quoted_ident(src: str, i: int) -> Tuple[str, int]:
    i += 1
    start = i
    while i < len(src) and src[i] != '\'':
        if not is_valid_ident_char(src[i]):
            raise LexerError(
                f"Invalid character {src[i]!r} in identifier at position {i}")
        i += 1
    if i >= len(src):
        raise LexerError("Unterminated quoted identifier")
    return src[start:i], i


def is_not_eps(ident: str):
    if ident == '':
        raise LexerError("Empty identifier is reserved for epsilon")


def set_next_token(src: str, i: int) -> Tuple[SetToken, int]:
    match c := src[i]:
        case '{':
            return Token(SetTokenType.LBRACE), i+1
        case '}':
            return Token(SetTokenType.RBRACE), i+1
        case ',':
            return Token(SetTokenType.COMMA), i+1
        case '\'':
            ident_str, i = scan_quoted_ident(src, i)
            is_not_eps(ident_str)
            return Token(SetTokenType.IDENT, ident_str), i + 1
        case _ if c.isalnum():
            return Token(SetTokenType.IDENT, c), i + 1
        case _:
            raise LexerError(f"Unexpected character {c!r} at position {i}")


def lex_set(src: str) -> Iterator[SetToken]:
    return generic_lexer(src, set_next_token, SetTokenType)
