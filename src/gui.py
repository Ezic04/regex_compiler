# type: ignore
import traceback
import networkx as nx
import matplotlib.pyplot as plt
from tkinter import Frame, Text, Button, Label, Scrollbar, Entry, BOTH, RIGHT, Y, LEFT, END, TOP, BOTTOM, DISABLED, NORMAL, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sys

from typing import Optional, Union

from regex.lexer import lex_regex
from regex.parser import parse_regex
from regex.to_epsnfa import regex_to_epsnfa
from automaton.convert import convert_to_nfa, convert_to_dfa
from automaton.lexer import lex_automaton
from automaton.parser import parse_automaton
from automaton.fsm import DFA, NFA, EpsNFA
from regex.ast import Expr
from typedef import Symbol
from common.parser_utils import ParserError

FSMType = Union[DFA, NFA, EpsNFA]


def _format_value(value) -> str:
    attr = getattr(value, "value", None)
    if attr is not None:
        return str(attr)
    return str(value)


def fsm_to_networkx(fsm: FSMType):
    G = nx.MultiDiGraph()
    for s in fsm.STATES:
        label = _format_value(s)
        G.add_node(label, initial=(s == fsm.INITIAL_STATE), accepting=(
            s in getattr(fsm, "ACCEPTING_STATES", set())))
    for (s, a), tgt in getattr(fsm, "TRANSITIONS", {}).items():
        s_label = _format_value(s)
        symbol_label = _format_value(a)
        if symbol_label == "":
            symbol_label = "ε"
        if isinstance(tgt, (set, frozenset)):
            for t in tgt:
                G.add_edge(s_label, _format_value(t), label=symbol_label)
        else:
            G.add_edge(s_label, _format_value(tgt), label=symbol_label)
    for s, targets in getattr(fsm, "EPS_TRANSITIONS", {}).items():
        for t in targets:
            G.add_edge(_format_value(s), _format_value(t), label="ε")
    return G


def draw_fsm_on_axes(ax: plt.axis, fsm: FSMType):
    ax.clear()
    G = fsm_to_networkx(fsm)
    pos = nx.spring_layout(G, seed=1)

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

    edge_labels = {}
    for u, v, data in G.edges(data=True):
        key = (u, v)
        edge_labels.setdefault(key, []).append(data.get("label", ""))
    nx.draw_networkx_edges(G, pos, ax=ax, connectionstyle="arc3,rad=0.1",
                           arrows=True, arrowsize=20, arrowstyle='->',
                           node_size=1200, min_source_margin=15, min_target_margin=15)
    formatted = {k: ",".join(sorted(set(v))) for k, v in edge_labels.items()}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=formatted, ax=ax)
    ax.set_axis_off()
    return ax


class AutomatonGUI:
    def __init__(self, root) -> None:
        self.root = root
        root.title("Automaton GUI")

        top = Frame(root)
        top.pack(side=TOP, fill=BOTH, expand=False)

        self.current_fsm: Optional[FSMType] = None

        Label(top, text="Regex input:").pack(anchor="w")
        self.regex_text = Text(top, height=3, width=60)
        self.regex_text.pack(fill=BOTH, expand=False)

        Label(top, text="Automaton spec input:").pack(anchor="w")
        frame_spec = Frame(top)
        frame_spec.pack(fill=BOTH, expand=False)
        self.spec_text = Text(frame_spec, height=6, width=60)
        self.spec_text.pack(side=LEFT, fill=BOTH, expand=True)
        scroll = Scrollbar(frame_spec, command=self.spec_text.yview)
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

        test_frame = Frame(top)
        test_frame.pack(fill=BOTH, expand=False, pady=(8, 0))
        Label(test_frame, text="Test word:").pack(side=LEFT, padx=(0, 4))
        self.test_entry = Entry(test_frame, width=30)
        self.test_entry.pack(side=LEFT, padx=4)
        Button(test_frame, text="Check Acceptance",
               command=self.on_check_word).pack(side=LEFT, padx=4)
        self.acceptance_label = Label(test_frame, text="", width=20)
        self.acceptance_label.pack(side=LEFT, padx=4)

        fig, ax = plt.subplots(figsize=(6, 5))
        self.fig = fig
        self.ax = ax
        canvas = FigureCanvasTkAgg(fig, master=root)
        canvas.get_tk_widget().pack(fill=BOTH, expand=True)
        self.canvas: FigureCanvasTkAgg = canvas

        self.status = Label(root, text="Ready")
        self.status.pack(side=BOTTOM, fill=BOTH)
        self.update_conversion_buttons()

        root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def set_status(self, text: str) -> None:
        self.status.config(text=text)

    def clear(self) -> None:
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
        draw_fsm_on_axes(self.ax, fsm)
        self.canvas.draw()

    def set_current_fsm(self, fsm: FSMType) -> None:
        self.current_fsm = fsm
        self.update_conversion_buttons()
        self.render_and_update(fsm)

    def update_conversion_buttons(self) -> None:
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
        plt.close('all')
        self.root.quit()
        self.root.destroy()
        sys.exit(0)
