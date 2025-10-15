from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Expr:
    """Base class for regex AST nodes."""
    pass


@dataclass(frozen=True, slots=True)
class Symbol(Expr):
    """A symbol in the regex."""
    value: str


@dataclass(frozen=True, slots=True)
class Star(Expr):
    """The Kleene star operator."""
    value: Expr


@dataclass(frozen=True, slots=True)
class Concat(Expr):
    """Concatenation of two regex expressions."""
    lhs: Expr
    rhs: Expr


@dataclass(frozen=True, slots=True)
class Or(Expr):
    """Alternation (logical OR) of two regex expressions."""
    lhs: Expr
    rhs: Expr
