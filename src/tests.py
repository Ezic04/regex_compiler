from regex.lexer import lex_regex
from regex.parser import parse_regex
from regex.to_epsnfa import regex_to_epsnfa
from automaton.convert import convert_to_nfa, convert_to_dfa
from automaton.lexer import lex_automaton
from automaton.parser import parse_automaton
from automaton.fsm import DFA, NFA, EpsNFA
from typedef import Symbol, State


def tests() -> None:
    inp = "(1|2)*33*"
    regex_ast = parse_regex(lex_regex(inp))
    regex_fsm = convert_to_dfa(convert_to_nfa(regex_to_epsnfa(regex_ast)))
    print(regex_fsm.accepts(map(Symbol, "3333123")))

    inp = "Q = {i, q, f};A = {0, 1};I = i;F = {f};(i, 1) -> {q, f};(q, 0) -> {f};(q,'') -> {f};(f, 0) -> {f};"
    fsm = parse_automaton(lex_automaton(inp))
    print(fsm.accepts(map(Symbol, "101")))

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
            (State('r'), Symbol('1')): State('r')
        }
    )
    print(dfa.accepts(map(Symbol, "110110110")))

    nfa = NFA(
        map(State, {'p', 'q'}),
        map(Symbol, {'0', '1'}),
        State('p'),
        map(State, {'q'}),
        {
            (State('p'), Symbol('1')): set(map(State, {'p', 'q'})),
            (State('p'), Symbol('0')): {State('p')}
        }
    )
    print(nfa.accepts(map(Symbol, "011010101011")))

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
            (State('s4'), Symbol('1')): {State('s3')}
        },
        {
            State('s0'): {State('s1')},
            State('s0'): {State('s3')}
        }
    )
    print(enfa.accepts(map(Symbol, "10101")))

    converted = convert_to_nfa(enfa)
    print(converted.accepts(map(Symbol, "10101")))

    converted = convert_to_nfa(enfa)
    print(converted.accepts(map(Symbol, "10101")))
