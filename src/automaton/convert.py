from typing import FrozenSet, Set, Dict, Tuple, List
from typedef import State, Symbol
from .fsm import DFA, NFA, EpsNFA

# pyright: reportPrivateUsage=false


def convert_to_nfa(eps_nfa: EpsNFA) -> NFA:
    closures: Dict[State, Set[State]] = {
        state: eps_nfa._eps_closure({state}) for state in eps_nfa.STATES
    }
    accepting_states: Set[State] = {
        state for state, cl in closures.items()
        if cl & eps_nfa.ACCEPTING_STATES
    }
    transitions: Dict[Tuple[State, Symbol], Set[State]] = {}
    for state, closure in closures.items():
        for symbol in eps_nfa.ALPHABET:
            reachable: Set[State] = {
                tgt for closure_state in closure
                for tgt in eps_nfa._delta(closure_state, symbol)
            }
            if not reachable:
                continue
            closure_reachable: Set[State] = eps_nfa._eps_closure(reachable)
            if closure_reachable:
                transitions[(state, symbol)] = closure_reachable
    return NFA(eps_nfa.STATES, eps_nfa.ALPHABET, eps_nfa.INITIAL_STATE, accepting_states, transitions)


def convert_to_dfa(nfa: NFA) -> DFA:
    def collapse_state(states: FrozenSet[State]) -> State:
        label = "{" + ",".join(sorted(map(str, states))) + "}"
        return State(label)
    initial_state_set: FrozenSet[State] = frozenset({nfa.INITIAL_STATE})
    accepting_states: Set[State] = set()
    transitions: Dict[Tuple[State, Symbol], State] = {}
    mapping: Dict[FrozenSet[State], State] = {
        initial_state_set: collapse_state(initial_state_set)}
    stack: List[FrozenSet[State]] = [initial_state_set]
    while stack:
        state_set = stack.pop()
        state = mapping[state_set]
        for symbol in nfa.ALPHABET:
            new_set = frozenset(
                q for p in state_set for q in nfa._delta(p, symbol)
            )
            if not (new_state := mapping.get(new_set)):
                new_state = collapse_state(new_set)
                mapping[new_set] = new_state
                if new_set & nfa.ACCEPTING_STATES:
                    accepting_states.add(new_state)
                stack.append(new_set)
            transitions[(state, symbol)] = new_state
    return DFA(
        set(mapping.values()),
        nfa.ALPHABET,
        mapping[initial_state_set],
        accepting_states,
        transitions
    )
