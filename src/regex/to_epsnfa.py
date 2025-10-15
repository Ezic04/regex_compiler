from .ast import Expr, Symbol, Star, Concat, Or
from automaton.fsm import EpsNFA
from common.typedef import Symbol


def regex_to_epsnfa(expr: Expr) -> EpsNFA:  # AI gen
    """Convert a regex AST to an equivalent epsilon-NFA."""
    if isinstance(expr, Symbol):
        return EpsNFA.from_symbol(Symbol(expr.value))
    elif isinstance(expr, Star):
        return EpsNFA.star(regex_to_epsnfa(expr.value))
    elif isinstance(expr, Concat):
        return EpsNFA.concat(regex_to_epsnfa(expr.lhs), regex_to_epsnfa(expr.rhs))
    elif isinstance(expr, Or):
        return EpsNFA.union(regex_to_epsnfa(expr.lhs), regex_to_epsnfa(expr.rhs))
    else:
        raise TypeError(f"Unknown regex AST node: {expr}")
