# type: ignore
from common.parser_utils import ParserError
from common.typedef import Symbol
from regex.ast import Expr
from automaton.fsm import DFA, NFA, EpsNFA
from automaton.parser import parse_automaton
from automaton.lexer import lex_automaton
from automaton.convert import convert_to_nfa, convert_to_dfa
from regex.to_epsnfa import regex_to_epsnfa
from regex.parser import parse_regex
from regex.lexer import lex_regex
from typing import Optional, Union, List
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import Frame, Text, Button, Label, Scrollbar, Entry, BOTH, RIGHT, Y, LEFT, END, TOP, BOTTOM, DISABLED, NORMAL, messagebox
import matplotlib.pyplot as plt
import networkx as nx
import traceback
import sys


FSMType = Union[DFA, NFA, EpsNFA]


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
                               node_size=1200, ax=ax, node_shape='s')  # square for initial
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


class RegexGUI:
    """GUI for regex/automaton visualization with conversion and word testing.

    Attributes:
        root: Tkinter root window.
        current_fsm: Currently loaded FSM (DFA, NFA, or EpsNFA).
        layout_seed: Seed for graph layout algorithm (increments on redraw).
        regex_text: Text widget for regex input.
        spec_text: Text widget for automaton specification input.
        test_entry: Entry widget for word acceptance testing.
        acceptance_label: Label showing acceptance test result.
        fig: Matplotlib figure for graph rendering.
        ax: Matplotlib axes for graph rendering.
        canvas: Matplotlib canvas embedded in tkinter.
        status: Status bar label.
        btn_eps_to_nfa: Button for ε-NFA to NFA conversion.
        btn_nfa_to_dfa: Button for NFA to DFA conversion.
    """

    def __init__(self, root) -> None:
        self.root = root
        root.title("RegexGUI")
        root.geometry("600x800")

        top = Frame(root)
        top.pack(side=TOP, fill=BOTH, expand=False)

        self.current_fsm: Optional[FSMType] = None
        self.layout_seed = 1

        input_frame = Frame(top)
        input_frame.pack(fill=BOTH, expand=False)

        left_frame = Frame(input_frame)
        left_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 5))
        Label(left_frame, text="Regex input:").pack(anchor="w")
        self.regex_text = Text(left_frame, height=5, width=30)
        self.regex_text.pack(fill=BOTH, expand=True)

        right_frame = Frame(input_frame)
        right_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(5, 0))
        Label(right_frame, text="Automaton spec input:").pack(anchor="w")
        spec_frame = Frame(right_frame)
        spec_frame.pack(fill=BOTH, expand=True)
        self.spec_text = Text(spec_frame, height=5, width=30)
        self.spec_text.pack(side=LEFT, fill=BOTH, expand=True)
        scroll = Scrollbar(spec_frame, command=self.spec_text.yview)
        scroll.pack(side=RIGHT, fill=Y)
        self.spec_text.config(yscrollcommand=scroll.set)

        btns = Frame(top)
        btns.pack(fill=BOTH, expand=False)
        Button(btns, text="Parse Regex and Show",
               command=self.on_parse_regex).pack(side=LEFT, padx=4, pady=4)
        Button(btns, text="Parse Automaton Spec and Show",
               command=self.on_parse_spec).pack(side=LEFT, padx=4, pady=4)
        Button(btns, text="Clear", command=self.clear).pack(
            side=LEFT, padx=4, pady=4)

        convert_frame = Frame(top)
        convert_frame.pack(fill=BOTH, expand=False)
        self.btn_eps_to_nfa = Button(
            convert_frame,
            text="Convert ε-NFA → NFA",
            command=self.on_convert_eps_to_nfa
        )
        self.btn_eps_to_nfa.pack(side=LEFT, padx=4, pady=4)
        self.btn_nfa_to_dfa = Button(
            convert_frame,
            text="Convert NFA → DFA",
            command=self.on_convert_nfa_to_dfa
        )
        self.btn_nfa_to_dfa.pack(side=LEFT, padx=4, pady=4)
        Button(convert_frame, text="Redraw Graph",
               command=self.on_redraw).pack(side=LEFT, padx=4, pady=4)

        test_frame = Frame(top)
        test_frame.pack(fill=BOTH, expand=False, pady=(8, 0))
        Label(test_frame, text="Test word:").pack(side=LEFT, padx=(0, 4))
        self.test_entry = Entry(test_frame, width=30)
        self.test_entry.pack(side=LEFT, padx=4)
        Button(test_frame, text="Check Acceptance",
               command=self.on_check_word).pack(side=LEFT, padx=4)
        self.acceptance_label = Label(test_frame, text="", width=20)
        self.acceptance_label.pack(side=LEFT, padx=4)

        fig, ax = plt.subplots(figsize=(6, 8))
        self.fig = fig
        self.ax = ax
        self.ax.set_axis_off()
        canvas = FigureCanvasTkAgg(fig, master=root)
        canvas.get_tk_widget().pack(fill=BOTH, expand=True)
        self.canvas: FigureCanvasTkAgg = canvas

        self.status = Label(root, text="Ready")
        self.status.pack(side=BOTTOM, fill=BOTH)
        self.update_conversion_buttons()

        root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def set_status(self, text: str) -> None:
        """Update status bar message."""
        self.status.config(text=text)

    def clear(self) -> None:
        """Clear all inputs and current automaton."""
        self.regex_text.delete("1.0", END)
        self.spec_text.delete("1.0", END)
        self.current_fsm = None
        self.test_entry.delete(0, END)
        self.acceptance_label.config(text="")
        self.ax.clear()
        self.canvas.draw()
        self.set_status("Cleared")
        self.update_conversion_buttons()

    def safe_run(self, fn, *a, **kw) -> bool:
        """Execute function with error handling and GUI feedback."""
        try:
            fn(*a, **kw)
        except ParserError as e:
            self.set_status("Parser error")
            messagebox.showerror("Parser Error", str(e))
            return False
        except Exception as e:
            self.set_status("Error (see console)")
            error_msg: str = f"{type(e).__name__}: {str(e)}"
            messagebox.showerror("Error", error_msg)
            traceback.print_exc()
            return False
        return True

    def render_and_update(self, fsm: FSMType) -> None:
        """Draw FSM on canvas with current layout seed."""
        draw_fsm_on_axes(self.ax, fsm, self.layout_seed)
        self.canvas.draw()

    def on_redraw(self) -> None:
        """Redraw the current FSM with a new layout."""
        if self.current_fsm is None:
            self.set_status("No automaton to redraw")
            return
        self.layout_seed += 1
        self.render_and_update(self.current_fsm)
        self.set_status(f"Graph redrawn (layout #{self.layout_seed})")

    def set_current_fsm(self, fsm: FSMType) -> None:
        self.current_fsm = fsm
        self.update_conversion_buttons()
        self.render_and_update(fsm)

    def update_conversion_buttons(self) -> None:
        """Enable/disable conversion buttons based on current FSM type."""
        if self.current_fsm is None:
            self.btn_eps_to_nfa.config(state=DISABLED)
            self.btn_nfa_to_dfa.config(state=DISABLED)
            return
        if isinstance(self.current_fsm, EpsNFA):
            self.btn_eps_to_nfa.config(state=NORMAL)
        else:
            self.btn_eps_to_nfa.config(state=DISABLED)
        if isinstance(self.current_fsm, NFA) and not isinstance(self.current_fsm, (DFA, EpsNFA)):
            self.btn_nfa_to_dfa.config(state=NORMAL)
        else:
            self.btn_nfa_to_dfa.config(state=DISABLED)

    def on_convert_eps_to_nfa(self) -> None:
        """Convert the current ε-NFA to an NFA."""
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

    def on_convert_nfa_to_dfa(self) -> None:
        """Convert the current NFA to a DFA."""
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

    def on_parse_regex(self) -> None:
        """Parse regex and build ε-NFA."""
        txt = self.regex_text.get("1.0", END).strip()
        if not txt:
            self.set_status("Empty regex input")
            return

        def work() -> None:
            ast: Expr = parse_regex(lex_regex(txt))
            eps: EpsNFA = regex_to_epsnfa(ast)
            self.set_current_fsm(eps)
        if self.safe_run(work):
            self.set_status("Parsed regex")

    def on_parse_spec(self) -> None:
        """Parse automaton specification and create FSM."""
        txt: str = self.spec_text.get("1.0", END).strip()
        if not txt:
            self.set_status("Empty spec input")
            return

        def work() -> None:
            fsm: FSMType = parse_automaton(lex_automaton(txt))
            self.set_current_fsm(fsm)
        if self.safe_run(work):
            self.set_status("Parsed spec")

    def on_check_word(self) -> None:
        """Test if current automaton accepts the input word."""
        if self.current_fsm is None:
            self.acceptance_label.config(text="No automaton loaded", fg="red")
            return

        word = self.test_entry.get().strip()
        try:
            symbols: List[Symbol] = [Symbol(c) for c in word]
            accepts: bool = self.current_fsm.accepts(symbols)
            if accepts:
                self.acceptance_label.config(text="✓ ACCEPTED", fg="green")
            else:
                self.acceptance_label.config(text="✗ REJECTED", fg="red")
        except Exception as e:
            self.acceptance_label.config(text="Error", fg="red")
            traceback.print_exc()

    def on_closing(self) -> None:
        """Clean up matplotlib and exit application."""
        plt.close('all')
        self.root.quit()
        self.root.destroy()
        sys.exit(0)
