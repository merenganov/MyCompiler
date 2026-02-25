import tkinter as tk
from tkinter import ttk


class Panels:
    # Paleta tipo VS Code (por defecto)
    BG = "#1e1e1e"
    FG = "#d4d4d4"
    SELECT_BG = "#264f78"
    CURSOR = "#ffffff"

    def __init__(self, parent):
        # Layout: arriba (explorador + editor + resultados); abajo (errores/ejecución)
        self.main_pane = ttk.Panedwindow(parent, orient=tk.VERTICAL)
        self.main_pane.pack(fill=tk.BOTH, expand=True)

        self.top_pane = ttk.Panedwindow(self.main_pane, orient=tk.HORIZONTAL)
        self.bottom_pane = ttk.Notebook(self.main_pane)

        self.main_pane.add(self.top_pane, weight=4)
        self.main_pane.add(self.bottom_pane, weight=2)

        # --- explorador (izquierda)
        self.explorer_container = ttk.Frame(self.top_pane)
        self.top_pane.add(self.explorer_container, weight=1)
        self._build_explorer(self.explorer_container)

        # --- contenedor del editor (centro)
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

    # ---------------- EXPLORER ----------------

    def _build_explorer(self, parent):
        header = ttk.Label(parent, text="EXPLORADOR DE PROYECTO")
        header.pack(anchor="w", padx=8, pady=(6, 2))

        self.project_tree = ttk.Treeview(parent, show="tree")
        self.project_tree.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

    # ---------------- TABS TEXT ----------------

    def _make_readonly_tab(self, notebook, title: str):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=title)

        text = tk.Text(
            frame,
            wrap="none",
            bg=self.BG,
            fg=self.FG,
            insertbackground=self.CURSOR,
            selectbackground=self.SELECT_BG,
            relief="flat",
            borderwidth=0
        )

        try:
            text.configure(font=("Consolas", 10))
        except Exception:
            pass

        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll_y = ttk.Scrollbar(frame, command=text.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        text.config(yscrollcommand=scroll_y.set)

        text.config(state="disabled")
        return text

    def set_text(self, widget: tk.Text, content: str):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("end", content)
        widget.config(state="disabled")

    # ---------------- THEME SUPPORT ----------------

    def apply_text_theme(self, bg, fg, cursor, select_bg):
        for widget in [
            self.lexico, self.sintactico, self.semantico, self.intermedio, self.simbolos,
            self.err_lex, self.err_sin, self.err_sem, self.exec_out
        ]:
            widget.configure(
                bg=bg,
                fg=fg,
                insertbackground=cursor,
                selectbackground=select_bg
            )