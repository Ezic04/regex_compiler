from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Expr:
    pass


@dataclass(frozen=True, slots=True)
class Symbol(Expr):
    value: str


@dataclass(frozen=True, slots=True)
class Star(Expr):
    value: Expr


@dataclass(frozen=True, slots=True)
class Concat(Expr):
    lhs: Expr
    rhs: Expr


@dataclass(frozen=True, slots=True)
class Or(Expr):
    lhs: Expr
    rhs: Expr


expr = Star(Concat(Symbol('1'), Or(Symbol('1'), Symbol('0'))))
