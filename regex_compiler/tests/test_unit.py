from ..regex.lexer import lex_regex
from ..regex.parser import parse_regex
from ..regex.to_epsnfa import regex_to_epsnfa
from ..automaton.convert import convert_to_nfa, convert_to_dfa
from ..automaton.lexer import lex_automaton
from ..automaton.parser import parse_automaton
from ..automaton.fsm import DFA, NFA, EpsNFA
from ..common.typedef import Symbol, State


def test_regex_pipeline():
    inp = "(1|2)*33*"
    regex_ast = parse_regex(lex_regex(inp))
    regex_fsm = convert_to_dfa(convert_to_nfa(regex_to_epsnfa(regex_ast)))

    assert regex_fsm.accepts(map(Symbol, "33"))
    assert regex_fsm.accepts(map(Symbol, "213"))
    assert not regex_fsm.accepts(map(Symbol, "3123"))
    assert not regex_fsm.accepts(map(Symbol, "121"))


def test_automaton_parser_accepts():
    inp = "Q = {i, q, f};A = {0, 1};I = i;F = {f};(i, 1) -> {q, f};(q, 0) -> {q};(q, 1) -> {f};(f, '') -> {i};"
    fsm = parse_automaton(lex_automaton(inp))
    assert fsm.accepts(map(Symbol, "1"))
    assert fsm.accepts(map(Symbol, "11"))
    assert fsm.accepts(map(Symbol, "101"))
    assert fsm.accepts(map(Symbol, "101101"))
    assert not fsm.accepts(map(Symbol, "1000"))
    assert not fsm.accepts(map(Symbol, "01"))


def test_dfa_accepts():
    dfa = DFA(
        map(State, {'p', 'q', 'r'}),
        map(Symbol, {'0', '1'}),
        State('p'),
        map(State, {'p'}),
        {
            (State('p'), Symbol('0')): State('p'),
            (State('p'), Symbol('1')): State('q'),
            (State('q'), Symbol('0')): State('r'),
            (State('q'), Symbol('1')): State('p'),
            (State('r'), Symbol('0')): State('q'),
            (State('r'), Symbol('1')): State('r'),
        }
    )

    assert dfa.accepts(map(Symbol, "110110110"))
    assert not dfa.accepts(map(Symbol, "111"))


def test_nfa_accepts():
    nfa = NFA(
        map(State, {'p', 'q'}),
        map(Symbol, {'0', '1'}),
        State('p'),
        map(State, {'q'}),
        {
            (State('p'), Symbol('1')): set(map(State, {'p', 'q'})),
            (State('p'), Symbol('0')): {State('p')},
        },
    )

    assert nfa.accepts(map(Symbol, "011010101011"))
    assert not nfa.accepts(map(Symbol, "000000"))


def test_conversion():
    enfa = EpsNFA(
        map(State, {'s0', 's1', 's2', 's3', 's4'}),
        map(Symbol, {'0', '1'}),
        State('s0'),
        map(State, {'s1', 's3'}),
        {
            (State('s1'), Symbol('1')): {State('s1')},
            (State('s1'), Symbol('0')): {State('s2')},
            (State('s2'), Symbol('1')): {State('s2')},
            (State('s2'), Symbol('0')): {State('s1')},
            (State('s3'), Symbol('0')): {State('s3')},
            (State('s3'), Symbol('1')): {State('s4')},
            (State('s4'), Symbol('0')): {State('s4')},
            (State('s4'), Symbol('1')): {State('s3')},
        },
        {
            State('s0'): {State('s1'), State('s3')},
        },
    )

    assert enfa.accepts(map(Symbol, "10101"))
    converted = convert_to_nfa(enfa)
    assert converted.accepts(map(Symbol, "10101"))
