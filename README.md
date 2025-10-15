# Regex Compiler & Automaton Visualizer

A Python GUI application for visualizing and converting finite state machines (FSM). Parse regular expressions or automaton specifications, visualize them as graphs, and convert between ε-NFA, NFA, and DFA.

## Features

- **Regex to ε-NFA**: Convert regular expressions to epsilon-NFAs
- **Automaton Parser**: Parse automaton specifications directly
- **Conversions**: ε-NFA → NFA → DFA with visual feedback
- **Word Testing**: Check if an automaton accepts a given word

## Usage

Run the GUI:
```bash
python src/main.py
```

### Input Examples

**Regex:**
```
(1|2)*33*
```

**Automaton Specification (ε-NFA):**
```
Q = {i, q, f};
A = {0, 1};
I = i;
F = {f};
(i, 1) -> {q, f};
(q, 0) -> {f};
(q,'') -> {f};
(f, 0) -> {f};
```

**DFA Example:**
```
Q = {p, q, r};
A = {0, 1};
I = p;
F = {p};
(p, 0) -> p;
(p, 1) -> q;
(q, 0) -> r;
(q, 1) -> p;
(r, 0) -> q;
(r, 1) -> r;
```

## Controls

- **Parse Regex and Show**: Convert regex to ε-NFA and visualize
- **Parse Automaton Spec and Show**: Parse and visualize automaton
- **Convert ε-NFA → NFA**: Eliminate epsilon transitions
- **Convert NFA → DFA**: Apply powerset construction
- **Redraw Graph**: Generate new layout (useful for overlapping nodes)
- **Test word**: Check if current automaton accepts input string
- **Clear**: Reset all inputs and visualization

## Visual Legend

- **Green Square**: Initial state
- **Gold circle with orange border**: Accepting state
- **Light blue circle**: Regular state
- **Green square with orange border**: Initial + accepting state

## Requirements

- Python 3.x
- tkinter
- matplotlib
- networkx