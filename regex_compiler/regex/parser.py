from typing import Iterator
from ..common.parser_utils import ParserError, Peekable, expect, expect_value
from .lexer import RegexTokenType, RegexToken
from .ast import Expr, Or, Concat, Star, Symbol


def parse_atom(tokens: Peekable[RegexToken]) -> Expr:
    """Parse an atomic regex expression (a symbol or a parenthesized expression)."""
    match tokens.peek().type:
        case RegexTokenType.LPAREN:
            tokens.next()
            expr: Expr = parse_or(tokens)
            expect(tokens, RegexTokenType.RPAREN)
        case RegexTokenType.IDENT:
            expr = Symbol(expect_value(tokens, RegexTokenType.IDENT))
        case _:
            raise ParserError(
                f"Expected token {RegexTokenType.IDENT} or "
                f"{RegexTokenType.LPAREN}, got {tokens.peek()!r}"
            )
    return expr


def parse_star(tokens: Peekable[RegexToken]) -> Expr:
    """Parse a star expression (an atom followed by a star)."""
    expr = parse_atom(tokens)
    if tokens.peek().type == RegexTokenType.STAR:
        tokens.next()
        expr = Star(expr)
    return expr


def parse_concat(tokens: Peekable[RegexToken]) -> Expr:
    """Parse a concatenation of regex expressions."""
    lhs: Expr = parse_star(tokens)
    while tokens.peek().type in {RegexTokenType.IDENT, RegexTokenType.LPAREN}:
        rhs: Expr = parse_star(tokens)
        lhs = Concat(lhs, rhs)
    return lhs


def parse_or(tokens: Peekable[RegexToken]) -> Expr:
    """Parse an alternation (logical OR) of regex expressions."""
    lhs: Expr = parse_concat(tokens)
    while tokens.peek().type == RegexTokenType.OR:
        tokens.next()
        rhs: Expr = parse_concat(tokens)
        lhs = Or(lhs, rhs)
    return lhs


def parse_regex(tokens: Iterator[RegexToken]) -> Expr:
    """Parse a full regex expression from tokens."""
    tokens = Peekable(tokens)
    expr = parse_or(tokens)
    expect(tokens, RegexTokenType.EOF)
    return expr
