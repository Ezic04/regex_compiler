from __future__ import annotations
from typing import Generic, TypeVar, Set, Dict, Tuple, FrozenSet, Iterable, List
from abc import ABC, abstractmethod
from functools import reduce
from typedef import State, Symbol


class FSMError(Exception):
    pass


TransitionResult = TypeVar("TransitionResult", Set[State], State)


class FSM(Generic[TransitionResult], ABC):
    def __init__(
            self,
            states: Iterable[State],
            alphabet: Iterable[Symbol],
            initial_state: State,
            accepting_states: Iterable[State],
            transitions: Dict[Tuple[State, Symbol], TransitionResult]
    ) -> None:
        self.STATES: FrozenSet[State] = frozenset(states)
        self.ALPHABET: FrozenSet[Symbol] = frozenset(alphabet)
        self.INITIAL_STATE: State = initial_state
        if self.INITIAL_STATE not in self.STATES:
            raise FSMError("Initial state not in states")
        self.ACCEPTING_STATES: FrozenSet[State] = frozenset(accepting_states)
        if invalid := self.ACCEPTING_STATES - self.STATES:
            raise FSMError(f"Invalid accepting states: {invalid}")
        if invalid := {key[0] for key in transitions.keys()} - self.STATES:
            raise FSMError(f"Invalid states in transitions keys : {invalid}")
        if invalid := {key[1] for key in transitions.keys()} - self.ALPHABET:
            raise FSMError(f"Invalid symbols in transitions values: {invalid}")
        if invalid := {s for val in transitions.values() for s in (val if isinstance(val, set) else {val})} - self.STATES:
            raise FSMError(f"Invalid states in transitions: {invalid}")
        self.TRANSITIONS: Dict[Tuple[State, Symbol],
                               TransitionResult] = transitions

    @abstractmethod
    def _delta(self, state: State, symbol: Symbol) -> TransitionResult:
        pass

    @abstractmethod
    def accepts(self, word: Iterable[Symbol]) -> bool:
        pass


class DFA(FSM[State]):
    def _delta(self, state: State, symbol: Symbol) -> State:
        return self.TRANSITIONS[(state, symbol)]

    def accepts(self, word: Iterable[Symbol]) -> bool:
        return reduce(self._delta, word, self.INITIAL_STATE) in self.ACCEPTING_STATES


class NFA(FSM[Set[State]]):
    def _delta(self, state: State, symbol: Symbol) -> Set[State]:
        return self.TRANSITIONS.get((state, symbol), set())

    def _get_initial_state_set(self) -> Set[State]:
        return {self.INITIAL_STATE}

    def _next_states(self, states: Set[State], symbol: Symbol) -> Set[State]:
        return {next_state for state in states for next_state in self._delta(state, symbol)}

    def accepts(self, word: Iterable[Symbol]) -> bool:
        return bool(self.ACCEPTING_STATES & reduce(self._next_states, word, self._get_initial_state_set()))


class EpsNFA(NFA):
    _id_counter = 0

    def __init__(
            self,
            states: Iterable[State],
            alphabet: Iterable[Symbol],
            initial_state: State,
            accepting_states: Iterable[State],
            transitions: Dict[Tuple[State, Symbol], Set[State]],
            eps_transitions: Dict[State, Set[State]]
    ) -> None:
        super().__init__(states, alphabet,  initial_state, accepting_states, transitions)
        if invalid := {key for key in eps_transitions.keys()} - self.STATES:
            raise FSMError(
                f"Invalid states in epsilon transitions keys: {invalid}")
        if invalid := {s for val in eps_transitions.values() for s in val} - self.STATES:
            raise FSMError(
                f"Invalid states in epsilon transitions values: {invalid}")
        self.EPS_TRANSITIONS:  Dict[State, Set[State]] = eps_transitions

    def _eps_delta(self, state: State) -> Set[State]:
        return self.EPS_TRANSITIONS.get(state, set())

    def _eps_closure(self, states: Set[State]) -> Set[State]:
        closure: Set[State] = set(states)
        stack: List[State] = list(states)
        while stack:
            state: State = stack.pop()
            for next_state in self._eps_delta(state):
                if not next_state in closure:
                    closure.add(next_state)
                    stack.append(next_state)
        return closure

    def _get_initial_state_set(self) -> Set[State]:
        return self._eps_closure(super()._get_initial_state_set())

    def _next_states(self, states: Set[State], symbol: Symbol) -> Set[State]:
        return self._eps_closure({
            next_state
            for state in self._eps_closure(states)
            for next_state in self._delta(state, symbol)
        })

    @classmethod
    def _fresh_state(cls, base: str = "S") -> State:
        cls._id_counter += 1
        return State(f"{base}{cls._id_counter}")

    @classmethod
    def _rename_states(cls, nfa: EpsNFA, prefix: str) -> Tuple[Dict[State, State], EpsNFA]:
        mapping: Dict[State, State] = {
            s: cls._fresh_state(prefix) for s in nfa.STATES}
        new_transitions: Dict[Tuple[State, Symbol], Set[State]] = {
            (mapping[state], symbol): {mapping[t] for t in targets}
            for (state, symbol), targets in nfa.TRANSITIONS.items()
        }
        new_eps_transitions: Dict[State, Set[State]] = {mapping[s]: {
            mapping[t] for t in targets} for s, targets in nfa.EPS_TRANSITIONS.items()}
        return mapping, EpsNFA(
            set(mapping.values()),
            nfa.ALPHABET,
            mapping[nfa.INITIAL_STATE],
            {mapping[s] for s in nfa.ACCEPTING_STATES},
            new_transitions,
            new_eps_transitions
        )

    @classmethod
    def from_symbol(cls, symbol: Symbol) -> EpsNFA:
        initial_state = cls._fresh_state("symbol")
        accepting_state = cls._fresh_state("symbol")
        return EpsNFA({initial_state, accepting_state}, {symbol}, initial_state, {accepting_state}, {(initial_state, symbol): {accepting_state}}, {})

    @classmethod
    def star(cls, operand: EpsNFA) -> EpsNFA:
        _, operand = cls._rename_states(operand, "star")
        initial_state = cls._fresh_state("star")
        return EpsNFA(
            {initial_state} | operand.STATES,
            operand.ALPHABET,
            initial_state,
            {initial_state},
            operand.TRANSITIONS,
            {
                **{s: targets | {initial_state} for s, targets in operand.EPS_TRANSITIONS.items()},
                **{s: {initial_state} for s in operand.ACCEPTING_STATES},
                initial_state: {operand.INITIAL_STATE}
            }
        )

    @classmethod
    def concat(cls, lhs: EpsNFA, rhs: EpsNFA) -> EpsNFA:
        _, lhs = cls._rename_states(lhs, "concat_lhs")
        _, rhs = cls._rename_states(rhs, "concat_rhs")
        keys = lhs.ACCEPTING_STATES | lhs.EPS_TRANSITIONS.keys() | rhs.EPS_TRANSITIONS.keys()

        def merge_eps(s: State) -> Set[State]:
            return set({rhs.INITIAL_STATE} if s in lhs.ACCEPTING_STATES else set()) | \
                lhs.EPS_TRANSITIONS.get(s, set()) | \
                rhs.EPS_TRANSITIONS.get(s, set())
        new_eps = {s: merge_eps(s) for s in keys}
        return EpsNFA(
            lhs.STATES | rhs.STATES,
            lhs.ALPHABET | rhs.ALPHABET,
            lhs.INITIAL_STATE,
            rhs.ACCEPTING_STATES,
            lhs.TRANSITIONS | rhs.TRANSITIONS,
            new_eps
        )

    @classmethod
    def union(cls, lhs: "EpsNFA", rhs: "EpsNFA") -> "EpsNFA":
        _, lhs = cls._rename_states(lhs, "union_lhs")
        _, rhs = cls._rename_states(rhs, "union_rhs")
        initial_state = cls._fresh_state("union")
        return EpsNFA(
            {initial_state} | lhs.STATES | rhs.STATES,
            lhs.ALPHABET | rhs.ALPHABET,
            initial_state,
            lhs.ACCEPTING_STATES | rhs.ACCEPTING_STATES,
            lhs.TRANSITIONS | rhs.TRANSITIONS,
            {initial_state: {lhs.INITIAL_STATE, rhs.INITIAL_STATE}} |
            lhs.EPS_TRANSITIONS | rhs.EPS_TRANSITIONS
        )
