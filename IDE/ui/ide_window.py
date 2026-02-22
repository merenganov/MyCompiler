import tkinter as tk
from tkinter import ttk, font

from core.state import IDEState
from core.file_manager import FileManager
from ui.menu import IDEMenu
from ui.toolbar import Toolbar
from ui.panels import Panels


class IDEWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("IDE")
        self.root.geometry("1100x700")

        self.state = IDEState()

        # ===== PANEL LAYOUT =====
        self.panels = Panels(self.root)

        # ===== STATUS BAR (CREAR ANTES DEL EDITOR) =====
        self.status = ttk.Label(self.root, text="Ln 1, Col 1", anchor="w")
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

        # ===== EDITOR =====
        self._build_editor(self.panels.editor_container)

        # ===== FILE MANAGER =====
        self.file_manager = FileManager(
            state=self.state,
            editor_text_widget=self.text_area,
            root=self.root,
            on_after_change=self._after_file_change
        )

        # ===== ACCIONES =====
        actions = {
            "new": self.file_manager.new_file,
            "open": self.file_manager.open_file,
            "close": self.file_manager.close_file,
            "save": self.file_manager.save,
            "save_as": self.file_manager.save_as,
            "exit": self.file_manager.exit_app,
            "compile_lex": self._ui_compile_lex,
            "compile_syn": self._ui_compile_syn,
            "compile_sem": self._ui_compile_sem,
            "compile_ir": self._ui_compile_ir,
            "run": self._ui_run,
        }

        # ===== MENÚ =====
        self.root.config(menu=IDEMenu(self.root, actions).build())

        # ===== TOOLBAR =====
        self.toolbar = Toolbar(self.root, actions)
        self.toolbar.pack()

        self._update_title()

    # ====================================================
    # =================== EDITOR =========================
    # ====================================================

    def _build_editor(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True)

        # Numeración
        self.line_numbers = tk.Canvas(
            frame,
            width=40,
            background="#eeeeee",
            highlightthickness=0
        )
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        # Scroll
        scroll = ttk.Scrollbar(frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Área de texto
        self.text_area = tk.Text(
            frame,
            wrap="none",
            undo=True,
            yscrollcommand=scroll.set
        )
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=self._on_scroll)

        # Eventos
        self.text_area.bind("<<Modified>>", self._on_modified)
        self.text_area.bind("<KeyRelease>", self._on_cursor_move)
        self.text_area.bind("<ButtonRelease-1>", self._on_cursor_move)
        self.text_area.bind("<MouseWheel>", self._on_mousewheel)
        self.text_area.bind("<Configure>", lambda e: self._redraw_line_numbers())

        self._redraw_line_numbers()
        self._update_cursor_status()

    def _on_scroll(self, *args):
        self.text_area.yview(*args)
        self._redraw_line_numbers()

    def _on_mousewheel(self, event):
        self._redraw_line_numbers()

    def _on_modified(self, event=None):
        if self.text_area.edit_modified():
            self.state.is_dirty = True
            self.text_area.edit_modified(False)
            self._update_title()
            self._redraw_line_numbers()

    def _on_cursor_move(self, event=None):
        self._update_cursor_status()
        self._redraw_line_numbers()

    def _update_cursor_status(self):
        pos = self.text_area.index(tk.INSERT)
        line, col = pos.split(".")
        self.status.config(text=f"Ln {line}, Col {int(col) + 1}")

    def _redraw_line_numbers(self):
        self.line_numbers.delete("all")

        f = font.Font(font=self.text_area["font"])
        line_height = f.metrics("linespace")

        first = int(self.text_area.index("@0,0").split(".")[0])
        last = int(self.text_area.index(f"@0,{self.text_area.winfo_height()}").split(".")[0])

        for line in range(first, last + 1):
            dline = self.text_area.dlineinfo(f"{line}.0")
            if dline:
                y = dline[1]
                self.line_numbers.create_text(28, y, anchor="ne", text=str(line))

    # ====================================================
    # ============== FILE CALLBACKS ======================
    # ====================================================

    def _after_file_change(self, status: str):
        self.status.config(text=status)
        self._update_title()
        self._redraw_line_numbers()

    def _update_title(self):
        name = self.state.current_file if self.state.current_file else "Nuevo Archivo"
        star = "*" if self.state.is_dirty else ""
        self.root.title(f"IDE - {name}{star}")

    # ====================================================
    # ============== UI PLACEHOLDERS =====================
    # ====================================================

    def _ui_compile_lex(self):
        self.panels.results_notebook.select(0)
        self.panels.set_text(self.panels.lexico, "Resultado Léxico (placeholder)\n")

    def _ui_compile_syn(self):
        self.panels.results_notebook.select(1)
        self.panels.set_text(self.panels.sintactico, "Resultado Sintáctico (placeholder)\n")

    def _ui_compile_sem(self):
        self.panels.results_notebook.select(2)
        self.panels.set_text(self.panels.semantico, "Resultado Semántico (placeholder)\n")

    def _ui_compile_ir(self):
        self.panels.results_notebook.select(3)
        self.panels.set_text(self.panels.intermedio, "Código Intermedio (placeholder)\n")

    def _ui_run(self):
        self.panels.bottom_pane.select(3)
        self.panels.set_text(self.panels.exec_out, "Ejecución (placeholder)\n")