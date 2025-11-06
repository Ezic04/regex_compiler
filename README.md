# Regex Compiler & Automaton Visualizer

A Python GUI application for visualizing and converting finite state machines (FSM). Parse regular expressions or automaton specifications, visualize them as graphs, and convert between ε-NFA, NFA, and DFA.

## Features

- **Regex to ε-NFA**: Convert regular expressions to epsilon-NFAs
- **Automaton Parser**: Parse automaton specifications directly
- **Conversions**: ε-NFA → NFA → DFA with visual feedback
- **Word Testing**: Check if an automaton accepts a given word

## Usage

### 1) Prebuilt binary (Linux)
If you prefer not to install Python or dependencies, a prebuilt Linux (x86_64) binary may be available under the repository's Releases. Download `regex_compiler`, make it executable, and run it:

```bash
chmod +x regex_compiler
./regex_compiler
```

### 2) Run from source
Set up a virtual environment, install dependencies, and start the GUI:

```bash
# create & activate venv
python -m venv .venv
source .venv/bin/activate

# install dependencies
pip install -r requirements.txt

# run the app
python -m regex_compiler.main
```

### 3) Build a single executable
Install PyInstaller (not included in requirements.txt) and build a one-file binary:

```bash
pip install pyinstaller
pyinstaller --onefile --name regex_compiler regex_compiler/main.py
```

The resulting binary will be at `dist/regex_compiler`.

## Input Examples

**Regex:**
```
(1|2)*33*
```

**Automaton Specification**

**ε-NFA Example:**
```
Q = {i, q, f};
A = {0, 1};
I = i;
F = {f};
(i, 1) -> {q, f};
(q, 0) -> {q};
(q, 1) -> {f};
(f, '') -> {i};
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


## Documentation

Documentation is generated with pdoc: pdoc src --output-dir docs --include-undocumented

## Tests

Tests are written with pytest.

Run the test suite:

```bash
pip install pytest
pytest
```



## Requirements

- Python 3.x
- PyQt5
- matplotlib
- networkx