# type: ignore
# AI gen
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTextEdit, QPushButton, QLabel,
                             QLineEdit, QMessageBox)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from .common.parser_utils import ParserError
from .common.typedef import Symbol
from .regex.ast import Expr
from .automaton.fsm import DFA, NFA, EpsNFA, FSMType
from .automaton.parser import parse_automaton
from .automaton.lexer import lex_automaton
from .automaton.convert import convert_to_nfa, convert_to_dfa
from .regex.to_epsnfa import regex_to_epsnfa
from .regex.parser import parse_regex
from .regex.lexer import lex_regex
from typing import Optional, List
import matplotlib.pyplot as plt
import networkx as nx
import traceback
import sys


def _format_value(value) -> str:
    """Extract display value from State/Symbol objects."""
    attr = getattr(value, "value", None)
    if attr is not None:
        return str(attr)
    return str(value)


def fsm_to_networkx(fsm: FSMType):
    """Convert FSM to NetworkX MultiDiGraph. Renames $-prefixed states to s1, s2, etc."""
    G = nx.MultiDiGraph()
    state_mapping = {}
    counter = 1
    for s in fsm.STATES:
        label = _format_value(s)
        if label.startswith('$'):
            state_mapping[label] = f's{counter}'
            counter += 1
        else:
            state_mapping[label] = label
    for s in fsm.STATES:
        original_label = _format_value(s)
        display_label = state_mapping[original_label]
        G.add_node(display_label, initial=(s == fsm.INITIAL_STATE), accepting=(
            s in fsm.ACCEPTING_STATES))
    edge_aggregator = {}
    for (s, a), tgt in fsm.TRANSITIONS.items():
        s_label = state_mapping[_format_value(s)]
        symbol_label = _format_value(a)
        if symbol_label == "":
            symbol_label = "ε"
        if isinstance(tgt, (set, frozenset)):
            for t in tgt:
                t_label = state_mapping[_format_value(t)]
                edge_key = (s_label, t_label)
                if edge_key not in edge_aggregator:
                    edge_aggregator[edge_key] = []
                edge_aggregator[edge_key].append(symbol_label)
        else:
            t_label = state_mapping[_format_value(tgt)]
            edge_key = (s_label, t_label)
            if edge_key not in edge_aggregator:
                edge_aggregator[edge_key] = []
            edge_aggregator[edge_key].append(symbol_label)

    for s, targets in getattr(fsm, "EPS_TRANSITIONS", {}).items():
        s_label = state_mapping[_format_value(s)]
        for t in targets:
            t_label = state_mapping[_format_value(t)]
            edge_key = (s_label, t_label)
            if edge_key not in edge_aggregator:
                edge_aggregator[edge_key] = []
            edge_aggregator[edge_key].append("ε")
    for (s_label, t_label), labels in edge_aggregator.items():
        combined_label = ",".join(sorted(set(labels)))
        G.add_edge(s_label, t_label, label=combined_label)
    return G


def draw_fsm_on_axes(ax: plt.axis, fsm: FSMType, layout_seed: int = 1):
    """Draw the FSM on the given matplotlib axes."""
    ax.clear()
    G = fsm_to_networkx(fsm)
    pos = nx.spring_layout(G, seed=layout_seed, k=1.5, iterations=50)
    initial_node = None
    accepting_nodes = []
    initial_accepting = []
    regular_nodes = []
    for node in G.nodes():
        is_initial = G.nodes[node].get('initial', False)
        is_accepting = G.nodes[node].get('accepting', False)
        if is_initial and is_accepting:
            initial_accepting.append(node)
        elif is_initial:
            initial_node = node
        elif is_accepting:
            accepting_nodes.append(node)
        else:
            regular_nodes.append(node)
    if regular_nodes:
        nx.draw_networkx_nodes(G, pos, nodelist=regular_nodes, node_color='lightblue',
                               node_size=1200, ax=ax)
    if initial_node:
        nx.draw_networkx_nodes(G, pos, nodelist=[initial_node], node_color='lightgreen',
                               node_size=1200, ax=ax, node_shape='s')
    if accepting_nodes:
        nx.draw_networkx_nodes(G, pos, nodelist=accepting_nodes, node_color='gold',
                               node_size=1200, ax=ax, linewidths=3, edgecolors='orange')
    if initial_accepting:
        nx.draw_networkx_nodes(G, pos, nodelist=initial_accepting, node_color='lightgreen',
                               node_size=1200, ax=ax, node_shape='s', linewidths=3, edgecolors='orange')
    node_labels = {n: n for n in G.nodes}
    nx.draw_networkx_labels(G, pos, labels=node_labels, ax=ax)
    edge_labels = {(u, v): data.get("label", "")
                   for u, v, data in G.edges(data=True)}
    nx.draw_networkx_edges(G, pos, ax=ax, connectionstyle="arc3,rad=0.1",
                           arrows=True, arrowsize=20, arrowstyle='->',
                           node_size=1200,
                           min_source_margin=15, min_target_margin=15)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax)
    ax.set_axis_off()
    return ax


class RegexGUI(QMainWindow):
    """GUI for regex/automaton visualization with conversion and word testing."""

    def __init__(self):
        super().__init__()
        self.current_fsm: Optional[FSMType] = None
        self.layout_seed = 1
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("RegexGUI")
        self.resize(600, 800)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Input frame with side-by-side text fields
        input_layout = QHBoxLayout()

        # Left side - Regex input
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Regex input:"))
        self.regex_text = QTextEdit()
        self.regex_text.setMaximumHeight(100)
        left_layout.addWidget(self.regex_text)
        input_layout.addLayout(left_layout)

        # Right side - Automaton spec input
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Automaton spec input:"))
        self.spec_text = QTextEdit()
        self.spec_text.setMaximumHeight(100)
        right_layout.addWidget(self.spec_text)
        input_layout.addLayout(right_layout)

        main_layout.addLayout(input_layout)

        # Buttons row 1
        btn_layout1 = QHBoxLayout()
        btn_parse_regex = QPushButton("Parse Regex and Show")
        btn_parse_regex.clicked.connect(self.on_parse_regex)
        btn_layout1.addWidget(btn_parse_regex)

        btn_parse_spec = QPushButton("Parse Automaton Spec and Show")
        btn_parse_spec.clicked.connect(self.on_parse_spec)
        btn_layout1.addWidget(btn_parse_spec)

        btn_clear = QPushButton("Clear")
        btn_clear.clicked.connect(self.clear)
        btn_layout1.addWidget(btn_clear)

        main_layout.addLayout(btn_layout1)

        # Buttons row 2 - Conversion
        btn_layout2 = QHBoxLayout()
        self.btn_eps_to_nfa = QPushButton("Convert ε-NFA → NFA")
        self.btn_eps_to_nfa.clicked.connect(self.on_convert_eps_to_nfa)
        btn_layout2.addWidget(self.btn_eps_to_nfa)

        self.btn_nfa_to_dfa = QPushButton("Convert NFA → DFA")
        self.btn_nfa_to_dfa.clicked.connect(self.on_convert_nfa_to_dfa)
        btn_layout2.addWidget(self.btn_nfa_to_dfa)

        btn_redraw = QPushButton("Redraw Graph")
        btn_redraw.clicked.connect(self.on_redraw)
        btn_layout2.addWidget(btn_redraw)

        main_layout.addLayout(btn_layout2)

        # Test word frame
        test_layout = QHBoxLayout()
        test_layout.addWidget(QLabel("Test word:"))
        self.test_entry = QLineEdit()
        test_layout.addWidget(self.test_entry)

        btn_check = QPushButton("Check Acceptance")
        btn_check.clicked.connect(self.on_check_word)
        test_layout.addWidget(btn_check)

        self.acceptance_label = QLabel("")
        self.acceptance_label.setMinimumWidth(150)
        test_layout.addWidget(self.acceptance_label)

        main_layout.addLayout(test_layout)

        # Matplotlib canvas
        self.fig = Figure(figsize=(6, 8))
        self.ax = self.fig.add_subplot(111)
        self.ax.set_axis_off()
        self.canvas = FigureCanvas(self.fig)
        main_layout.addWidget(self.canvas)

        # Status bar
        self.status_bar = self.statusBar()
        self.set_status("Ready")

        self.update_conversion_buttons()

    def set_status(self, text: str):
        """Update status bar message."""
        self.status_bar.showMessage(text)

    def clear(self):
        """Clear all inputs and current automaton."""
        self.regex_text.clear()
        self.spec_text.clear()
        self.current_fsm = None
        self.test_entry.clear()
        self.acceptance_label.setText("")
        self.ax.clear()
        self.ax.set_axis_off()
        self.canvas.draw()
        self.set_status("Cleared")
        self.update_conversion_buttons()

    def safe_run(self, fn, *a, **kw) -> bool:
        """Execute function with error handling and GUI feedback."""
        try:
            fn(*a, **kw)
        except ParserError as e:
            self.set_status("Parser error")
            QMessageBox.critical(self, "Parser Error", str(e))
            return False
        except Exception as e:
            self.set_status("Error (see console)")
            error_msg = f"{type(e).__name__}: {str(e)}"
            QMessageBox.critical(self, "Error", error_msg)
            traceback.print_exc()
            return False
        return True

    def render_and_update(self, fsm: FSMType):
        """Draw FSM on canvas with current layout seed."""
        draw_fsm_on_axes(self.ax, fsm, self.layout_seed)
        self.canvas.draw()

    def on_redraw(self):
        """Redraw the current FSM with a new layout."""
        if self.current_fsm is None:
            self.set_status("No automaton to redraw")
            return
        self.layout_seed += 1
        self.render_and_update(self.current_fsm)
        self.set_status(f"Graph redrawn (layout #{self.layout_seed})")

    def set_current_fsm(self, fsm: FSMType):
        self.current_fsm = fsm
        self.update_conversion_buttons()
        self.render_and_update(fsm)

    def update_conversion_buttons(self):
        """Enable/disable conversion buttons based on current FSM type."""
        if self.current_fsm is None:
            self.btn_eps_to_nfa.setEnabled(False)
            self.btn_nfa_to_dfa.setEnabled(False)
            return
        if isinstance(self.current_fsm, EpsNFA):
            self.btn_eps_to_nfa.setEnabled(True)
        else:
            self.btn_eps_to_nfa.setEnabled(False)
        if isinstance(self.current_fsm, NFA) and not isinstance(self.current_fsm, (DFA, EpsNFA)):
            self.btn_nfa_to_dfa.setEnabled(True)
        else:
            self.btn_nfa_to_dfa.setEnabled(False)

    def on_convert_eps_to_nfa(self):
        """Convert the current ε-NFA to an NFA."""
        self.layout_seed = 1
        if not isinstance(self.current_fsm, EpsNFA):
            self.set_status("Load an ε-NFA before converting to NFA")
            return
        try:
            converted: NFA = convert_to_nfa(self.current_fsm)
        except Exception:
            self.set_status("Conversion ε-NFA → NFA failed (see console)")
            traceback.print_exc()
            return
        self.set_status("Converted ε-NFA to NFA")
        self.set_current_fsm(converted)

    def on_convert_nfa_to_dfa(self):
        """Convert the current NFA to a DFA."""
        self.layout_seed = 1
        if self.current_fsm is None:
            self.set_status("No automaton to convert")
            return
        if isinstance(self.current_fsm, DFA):
            self.set_status("Current automaton is already a DFA")
            return
        if isinstance(self.current_fsm, EpsNFA):
            self.set_status("Convert ε-NFA to NFA before creating a DFA")
            return
        try:
            converted: DFA = convert_to_dfa(self.current_fsm)
        except Exception:
            self.set_status("Conversion NFA → DFA failed (see console)")
            traceback.print_exc()
            return
        self.set_status("Converted NFA to DFA")
        self.set_current_fsm(converted)

    def on_parse_regex(self):
        """Parse regex and build ε-NFA."""
        self.layout_seed = 1
        txt = self.regex_text.toPlainText().strip()
        if not txt:
            self.set_status("Empty regex input")
            return

        def work():
            ast: Expr = parse_regex(lex_regex(txt))
            eps: EpsNFA = regex_to_epsnfa(ast)
            self.set_current_fsm(eps)
        if self.safe_run(work):
            self.set_status("Parsed regex")

    def on_parse_spec(self):
        """Parse automaton specification and create FSM."""
        self.layout_seed = 1
        txt = self.spec_text.toPlainText().strip()
        if not txt:
            self.set_status("Empty spec input")
            return

        def work():
            fsm: FSMType = parse_automaton(lex_automaton(txt))
            self.set_current_fsm(fsm)
        if self.safe_run(work):
            self.set_status("Parsed spec")

    def on_check_word(self):
        """Test if current automaton accepts the input word."""
        self.layout_seed = 1
        if self.current_fsm is None:
            self.acceptance_label.setText("No automaton loaded")
            self.acceptance_label.setStyleSheet("color: red")
            return

        word = self.test_entry.text().strip()
        try:
            symbols: List[Symbol] = [Symbol(c) for c in word]
            accepts: bool = self.current_fsm.accepts(symbols)
            if accepts:
                self.acceptance_label.setText("✓ ACCEPTED")
                self.acceptance_label.setStyleSheet("color: green")
            else:
                self.acceptance_label.setText("✗ REJECTED")
                self.acceptance_label.setStyleSheet("color: red")
        except Exception as e:
            self.acceptance_label.setText("Error")
            self.acceptance_label.setStyleSheet("color: red")
            traceback.print_exc()

    def closeEvent(self, event):
        """Clean up matplotlib and exit application."""
        plt.close('all')
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = RegexGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
