from typing import Set, Iterator, Tuple, Optional, Iterable, Dict, TypeVar
from common.token import Token
from common.lexer_utils import lex_set
from common.parser_utils import ParserError, Peekable, expect, expect_value, parse_set
from typedef import Symbol, State
from utility import unwrap
from .lexer import TransitionTokenType, TransitionToken, AutomatonTokenType, AutomatonToken, lex_transition
from .fsm import DFA, NFA, EpsNFA


def parse_transition(tokens: Iterator[TransitionToken]) -> Tuple[State, Optional[Symbol], State | Set[State]]:
    tokens = Peekable(tokens)
    expect(tokens, TransitionTokenType.LPRENT)
    state = State(expect_value(tokens, TransitionTokenType.IDENT))
    expect(tokens, TransitionTokenType.COMMA)
    symbol = None if tokens.peek().type == TransitionTokenType.EPS and tokens.next() else Symbol(
        expect_value(tokens, TransitionTokenType.IDENT)
    )
    expect(tokens, TransitionTokenType.RPRENT)
    expect(tokens, TransitionTokenType.ARROW)
    token: Token[TransitionTokenType] = tokens.next()
    match token.type:
        case TransitionTokenType.IDENT:
            if symbol is None:
                raise ParserError(
                    "Epsilon transition must lead to a set of states")
            transition_result: State | Set[State] = State(unwrap(token.value))
        case TransitionTokenType.SET:
            transition_result = {State(s) for s in
                                 parse_set(lex_set(unwrap(token.value)))}
        case _:
            raise ParserError(
                f"Expected token {TransitionTokenType.IDENT!r} or "
                f"{TransitionTokenType.SET!r}, got {token!r}"
            )
    return state, symbol, transition_result


def parse_automaton(tokens: Iterator[AutomatonToken]) -> DFA | NFA | EpsNFA:
    tokens = Peekable(tokens)
    K = TypeVar("K")
    V = TypeVar("V")

    def add_unique_entry(
        mapping: Optional[Dict[K, V]],
        key: K, value: V,
        what: str = "transition"
    ) -> Dict[K, V]:
        mapping = mapping or {}
        if key in mapping:
            raise ParserError(f"Multiple {what}s for {key}")
        mapping[key] = value
        return mapping

    def is_alredy_defined(val: Optional[V], what: str):
        if val is not None:
            raise ParserError(what, " already defined")

    def get_set() -> Set[str]:
        return parse_set(lex_set(expect_value(tokens, AutomatonTokenType.SET)))

    states: Optional[Iterable[State]] = None
    alphabet: Optional[Iterable[Symbol]] = None
    initial_state: Optional[State] = None
    accepting_states: Optional[Iterable[State]] = None
    dfa_transitions: Optional[Dict[Tuple[State, Symbol], State]] = None
    nfa_transitions: Optional[Dict[Tuple[State, Symbol], Set[State]]] = None
    eps_transitions: Optional[Dict[State, Set[State]]] = None
    is_nfa: bool = False

    def handle_transition(token: AutomatonToken) -> None:
        nonlocal is_nfa, dfa_transitions, nfa_transitions, eps_transitions
        state, symbol, target = parse_transition(
            lex_transition(unwrap(token.value)))
        if symbol is None:
            is_nfa = True
            if not isinstance(target, set):
                raise ParserError(
                    "Epsilon transition must lead to a set of states")
            eps_transitions = add_unique_entry(
                eps_transitions, state, target, "epsilon transition")
        else:
            if isinstance(target, set) and dfa_transitions is not None:
                raise ParserError(
                    "NFA transitions must lead to a set of states")
            if not isinstance(target, set) and is_nfa:
                raise ParserError(
                    "DFA transitions must lead to a single state")
            if isinstance(target, set):
                is_nfa = True
                nfa_transitions = add_unique_entry(
                    nfa_transitions, (state, symbol), target)
            else:
                dfa_transitions = add_unique_entry(
                    dfa_transitions, (state, symbol), target)

    while (token := tokens.next()).type != AutomatonTokenType.EOF:
        if token.type == AutomatonTokenType.TRANS:
            handle_transition(token)
            expect(tokens, AutomatonTokenType.SEMICOLON)
            continue
        expect(tokens, AutomatonTokenType.EQ)
        match token.type:
            case AutomatonTokenType.STATES:
                is_alredy_defined(states, "States")
                states = map(State, get_set())
            case AutomatonTokenType.ALPHA:
                is_alredy_defined(alphabet, "Alphabet")
                alphabet = map(Symbol, get_set())
            case AutomatonTokenType.INIT:
                is_alredy_defined(initial_state, "Initial state")
                initial_state = State(expect_value(
                    tokens, AutomatonTokenType.IDENT))
            case AutomatonTokenType.ACCEPT:
                is_alredy_defined(accepting_states, "Accepting states")
                accepting_states = map(State, get_set())
            case _:
                raise ParserError(f"Unexpected token {token!r}")
        expect(tokens, AutomatonTokenType.SEMICOLON)
    if states is None:
        raise ParserError("States not defined")
    if alphabet is None:
        raise ParserError("Alphabet not defined")
    if initial_state is None:
        raise ParserError("Initial state not defined")
    if accepting_states is None:
        raise ParserError("Accepting states not defined")
    if dfa_transitions is None and nfa_transitions is None:
        raise ParserError("Transitions not defined")
    if eps_transitions is not None:
        return EpsNFA(states, alphabet, initial_state, accepting_states, nfa_transitions or {}, eps_transitions)
    return NFA(states, alphabet, initial_state, accepting_states, nfa_transitions or {}) if is_nfa else DFA(states, alphabet, initial_state, accepting_states, dfa_transitions or {})
