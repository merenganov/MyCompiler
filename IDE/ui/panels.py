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

        # La pestaña semántica conserva un área de texto para el resumen,
        # pero ahora también contiene un Treeview colapsable para el AST anotado.
        self.semantico = self._make_semantic_tab(self.results_notebook, "Semántico")

        self.intermedio = self._make_readonly_tab(self.results_notebook, "Intermedio")
        self.simbolos = self._make_readonly_tab(self.results_notebook, "Símbolos")

        # --- errores y ejecución (abajo)
        self.err_lex = self._make_readonly_tab(self.bottom_pane, "Errores Léxicos")
        self.err_sin = self._make_readonly_tab(self.bottom_pane, "Errores Sintácticos")
        self.err_sem = self._make_readonly_tab(self.bottom_pane, "Errores Semánticos")
        self.exec_out = self._make_readonly_tab(self.bottom_pane, "Ejecución")

    # ---------------- EXPLORER ----------------

    def _build_explorer(self, parent):
        # ===== Título =====
        header = ttk.Label(parent, text="EXPLORADOR DE PROYECTO")
        header.pack(anchor="w", padx=8, pady=(6, 2))

        # ===== Contenedor del árbol =====
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # ===== Treeview =====
        # Guardamos la ruta completa en columna oculta
        self.project_tree = ttk.Treeview(
            tree_frame,
            show="tree",
            columns=("fullpath",)
        )

        # Ocultamos la columna donde guardamos la ruta real
        self.project_tree.column("fullpath", width=0, stretch=False)

        self.project_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # ===== Scrollbar =====
        scroll_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.project_tree.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.project_tree.configure(yscrollcommand=scroll_y.set)

        # ===== Configuración opcional estilo =====
        self.project_tree.configure(selectmode="browse")

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

    def _make_semantic_tab(self, notebook, title: str):
        """
        Crea la pestaña Semántico con:
        - un área superior para el resumen del análisis;
        - un Treeview inferior para mostrar el AST anotado de forma
          expandible/colapsable.

        Se devuelve el widget Text del resumen para conservar compatibilidad
        con el código existente que usa self.panels.semantico.
        """
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=title)

        # Resumen del análisis semántico.
        summary = tk.Text(
            frame,
            height=3,
            wrap="word",
            bg=self.BG,
            fg=self.FG,
            insertbackground=self.CURSOR,
            selectbackground=self.SELECT_BG,
            relief="flat",
            borderwidth=0
        )

        try:
            summary.configure(font=("Consolas", 10))
        except Exception:
            pass

        summary.pack(side=tk.TOP, fill=tk.X)
        summary.config(state="disabled")

        # Separador visual entre resumen y árbol.
        separator = ttk.Separator(frame, orient=tk.HORIZONTAL)
        separator.pack(side=tk.TOP, fill=tk.X)

        # Contenedor del árbol semántico.
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.semantic_tree = ttk.Treeview(
            tree_frame,
            show="tree",
            selectmode="browse",
            style="Semantic.Treeview"
        )
        self.semantic_tree.heading(
            "#0",
            text="AST con Anotaciones Semánticas",
            anchor="w"
        )
        self.semantic_tree.column("#0", width=800, minwidth=300, stretch=True)

        scroll_y = ttk.Scrollbar(
            tree_frame,
            orient=tk.VERTICAL,
            command=self.semantic_tree.yview
        )
        scroll_x = ttk.Scrollbar(
            tree_frame,
            orient=tk.HORIZONTAL,
            command=self.semantic_tree.xview
        )

        self.semantic_tree.configure(
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )

        self.semantic_tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        return summary

    def set_text(self, widget: tk.Text, content: str):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("end", content)
        widget.config(state="disabled")

    # ---------------- ÁRBOL SEMÁNTICO ----------------

    def clear_semantic_tree(self):
        """Elimina todos los nodos del árbol semántico de la pestaña."""
        if not hasattr(self, "semantic_tree"):
            return

        children = self.semantic_tree.get_children("")
        if children:
            self.semantic_tree.delete(*children)

    def set_semantic_tree(self, root_node):
        """
        Muestra un AST anotado dentro de la pestaña Semántico.
        Cada nodo puede expandirse o colapsarse con las flechas del Treeview.
        """
        self.clear_semantic_tree()

        if root_node is None:
            return

        self._insert_semantic_node("", root_node)

    def _insert_semantic_node(self, parent_id, node):
        if hasattr(node, "semantic_str"):
            node_text = node.semantic_str()
        else:
            node_text = str(node)

        item_id = self.semantic_tree.insert(
            parent_id,
            "end",
            text=node_text,
            open=True
        )

        for child in getattr(node, "children", []):
            self._insert_semantic_node(item_id, child)

    # ---------------- THEME SUPPORT ----------------

    def apply_text_theme(self, bg, fg, cursor, select_bg):
        # Widgets de texto existentes.
        for widget in [
            self.lexico,
            self.sintactico,
            self.semantico,
            self.intermedio,
            self.simbolos,
            self.err_lex,
            self.err_sin,
            self.err_sem,
            self.exec_out
        ]:
            widget.configure(
                bg=bg,
                fg=fg,
                insertbackground=cursor,
                selectbackground=select_bg
            )

        # Tema del Treeview semántico.
        if hasattr(self, "semantic_tree"):
            style = ttk.Style()
            style.configure(
                "Semantic.Treeview",
                background=bg,
                foreground=fg,
                fieldbackground=bg,
                borderwidth=0,
                relief="flat"
            )
            style.map(
                "Semantic.Treeview",
                background=[("selected", select_bg)],
                foreground=[("selected", fg)]
            )
            self.semantic_tree.configure(style="Semantic.Treeview")
