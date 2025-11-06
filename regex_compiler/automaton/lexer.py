from enum import Enum, auto
from typing import Tuple, Iterator
from ..common.token import Token
from ..common.lexer_utils import LexerError,  generic_lexer, scan_quoted_ident, is_not_eps


class TransitionTokenType(Enum):
    """Token types for transitions in automata."""
    LPRENT = auto()
    RPRENT = auto()
    COMMA = auto()
    ARROW = auto()
    SET = auto()
    EPS = auto()
    IDENT = auto()
    EOF = auto()


TransitionToken = Token[TransitionTokenType]


def scan_set(src: str, i: int) -> tuple[str, int]:  # AI gen
    """Return the set literal starting at index i in src and the index of the closing brace."""
    start = i
    while i < len(src) and src[i] != '}':
        i += 1
    if i >= len(src):
        raise LexerError("Unterminated set literal")
    return src[start:i+1], i


def transition_next_token(src: str, i: int) -> Tuple[TransitionToken, int]:
    """Get the next token from the source string starting at index i."""
    match c := src[i]:
        case '(':
            return Token(TransitionTokenType.LPRENT), i+1
        case ')':
            return Token(TransitionTokenType.RPRENT), i+1
        case ',':
            return Token(TransitionTokenType.COMMA), i+1
        case '{':
            ident_str, i = scan_set(src, i)
            is_not_eps(ident_str)
            return Token(TransitionTokenType.SET, ident_str), i+1
        case '-' if i+1 < len(src) and src[i+1] == '>':
            return Token(TransitionTokenType.ARROW), i+2
        case '\'':
            token_text, i = scan_quoted_ident(src, i)
            if token_text == '':
                return Token(TransitionTokenType.EPS), i+1
            return Token(TransitionTokenType.IDENT, token_text), i+1
        case _ if c.isalnum():
            return Token(TransitionTokenType.IDENT, c), i+1
        case _:
            raise LexerError(f"Unexpected character {c!r} at position {i}")


def lex_transition(src: str) -> Iterator[TransitionToken]:
    """Lex the source string into transition tokens."""
    return generic_lexer(src, transition_next_token, TransitionTokenType)


class AutomatonTokenType(Enum):
    """Token types for automata definitions."""
    EQ = auto()
    SEMICOLON = auto()
    SET = auto()
    TRANS = auto()
    STATES = auto()
    ALPHA = auto()
    INIT = auto()
    ACCEPT = auto()
    IDENT = auto()
    EOF = auto()


AutomatonToken = Token[AutomatonTokenType]


def scan_transition(src: str, i: int) -> tuple[str, int]:  # AI gen
    """Return the transition literal starting at index i in src and the index of the closing semicolon."""
    start = i
    while i < len(src) and src[i] != ';':
        i += 1
    if i >= len(src):
        raise LexerError("Unterminated transition literal")
    return src[start:i], i


def automaton_next_token(src: str, i: int) -> Tuple[AutomatonToken, int]:
    """Get the next token from the source string starting at index i."""
    match c := src[i]:
        case ';':
            return Token(AutomatonTokenType.SEMICOLON), i+1
        case '=':
            return Token(AutomatonTokenType.EQ), i+1
        case '{':
            token_text, i = scan_set(src, i)
            return Token(AutomatonTokenType.SET, token_text), i+1
        case '(':
            token_text, i = scan_transition(src, i)
            return Token(AutomatonTokenType.TRANS, token_text), i
        case 'Q':
            return Token(AutomatonTokenType.STATES), i+1
        case 'A':
            return Token(AutomatonTokenType.ALPHA), i+1
        case 'I':
            return Token(AutomatonTokenType.INIT), i+1
        case 'F':
            return Token(AutomatonTokenType.ACCEPT), i+1
        case '\'':
            ident_str, i = scan_quoted_ident(src, i)
            is_not_eps(ident_str)
            return Token(AutomatonTokenType.IDENT, ident_str), i+1
        case _ if c.isalnum():
            return Token(AutomatonTokenType.IDENT, c), i+1
        case _:
            raise LexerError(f"Unexpected character {c!r} at position {i}")


def lex_automaton(src: str) -> Iterator[AutomatonToken]:
    """Lex the source string into automaton tokens."""
    return generic_lexer(src, automaton_next_token, AutomatonTokenType)
