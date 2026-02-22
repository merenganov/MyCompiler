import tkinter as tk
from tkinter import ttk

class Panels:
    def __init__(self, parent):
        # Layout: izquierda editor, derecha resultados; abajo errores/ejecución
        self.main_pane = ttk.Panedwindow(parent, orient=tk.VERTICAL)
        self.main_pane.pack(fill=tk.BOTH, expand=True)

        self.top_pane = ttk.Panedwindow(self.main_pane, orient=tk.HORIZONTAL)
        self.bottom_pane = ttk.Notebook(self.main_pane)

        self.main_pane.add(self.top_pane, weight=4)
        self.main_pane.add(self.bottom_pane, weight=2)

        # --- contenedor del editor (lo llena ide_window)
        self.editor_container = ttk.Frame(self.top_pane)
        self.top_pane.add(self.editor_container, weight=3)

        # --- resultados (derecha)
        self.results_container = ttk.Frame(self.top_pane)
        self.top_pane.add(self.results_container, weight=2)

        self.results_notebook = ttk.Notebook(self.results_container)
        self.results_notebook.pack(fill=tk.BOTH, expand=True)

        self.lexico = self._make_readonly_tab(self.results_notebook, "Léxico")
        self.sintactico = self._make_readonly_tab(self.results_notebook, "Sintáctico")
        self.semantico = self._make_readonly_tab(self.results_notebook, "Semántico")
        self.intermedio = self._make_readonly_tab(self.results_notebook, "Intermedio")
        self.simbolos = self._make_readonly_tab(self.results_notebook, "Símbolos")

        # --- errores y ejecución (abajo)
        self.err_lex = self._make_readonly_tab(self.bottom_pane, "Errores Léxicos")
        self.err_sin = self._make_readonly_tab(self.bottom_pane, "Errores Sintácticos")
        self.err_sem = self._make_readonly_tab(self.bottom_pane, "Errores Semánticos")
        self.exec_out = self._make_readonly_tab(self.bottom_pane, "Ejecución")

    def _make_readonly_tab(self, notebook, title: str):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=title)

        text = tk.Text(frame, wrap="word")
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll = ttk.Scrollbar(frame, command=text.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        text.config(yscrollcommand=scroll.set)

        text.config(state="disabled")
        return text

    def set_text(self, widget: tk.Text, content: str):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("end", content)
        widget.config(state="disabled")