import os
import tkinter as tk
from tkinter import ttk, font

from core.state import IDEState
from core.file_manager import FileManager
from ui.menu import IDEMenu
from ui.toolbar import Toolbar
from ui.panels import Panels


class IDEWindow:
    THEMES = {
        "dark": {
            "text_bg": "#1e1e1e",
            "text_fg": "#d4d4d4",
            "panel_bg": "#252526",
            "line_fg": "#858585",
            "select_bg": "#264f78",
            "cursor": "#ffffff",
        },
        "light": {
            "text_bg": "#ffffff",
            "text_fg": "#111111",
            "panel_bg": "#e6e6e6",
            "line_fg": "#666666",
            "select_bg": "#cce6ff",
            "cursor": "#000000",
        }
    }

    def __init__(self, root: tk.Tk, apply_theme_callback, default_theme: str = "dark"):
        self.root = root
        self.root.title("IDE")
        self.root.geometry("1100x700")

        self.apply_theme_callback = apply_theme_callback
        self.theme_mode = default_theme

        self.state = IDEState()
        actions = {}

        # =========================================================
        # CONTENEDORES: TOP (toolbar), CENTER (panels), BOTTOM (status)
        # =========================================================
        self.top_container = ttk.Frame(self.root)
        self.top_container.pack(side=tk.TOP, fill=tk.X)

        self.bottom_container = ttk.Frame(self.root)
        self.bottom_container.pack(side=tk.BOTTOM, fill=tk.X)

        self.center_container = ttk.Frame(self.root)
        self.center_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # ===== STATUS BAR (BOTTOM_CONTAINER) =====
        self.status = ttk.Label(self.bottom_container, text="Ln 1, Col 1", anchor="e")
        self.status.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=8)

        # ===== PANELS (CENTER) =====
        self.panels = Panels(self.center_container)

        # ===== EDITOR =====
        self._build_editor(self.panels.editor_container)

        # ===== FILE MANAGER =====
        self.file_manager = FileManager(
            state=self.state,
            editor_text_widget=self.text_area,
            root=self.root,
            on_after_change=self._after_file_change
        )

        # ===== EXPLORADOR (doble clic abre) =====
        if hasattr(self.panels, "project_tree"):
            self.panels.project_tree.bind("<Double-1>", self._on_tree_open)

        # ===== ACTIONS (TODO FUNCIONAL) =====
        actions.update({
            # Archivo
            "new": self.file_manager.new_file,
            "open": self.file_manager.open_file,
            "open_project": (lambda: self.file_manager.open_project_folder(self.panels.project_tree))
            if hasattr(self.panels, "project_tree") else (lambda: None),
            "close": self.file_manager.close_file,
            "save": self.file_manager.save,
            "save_as": self.file_manager.save_as,
            "exit": self.file_manager.exit_app,

            # Compilar (placeholders por ahora)
            "compile_lex": self._ui_compile_lex,
            "compile_syn": self._ui_compile_syn,
            "compile_sem": self._ui_compile_sem,
            "compile_ir": self._ui_compile_ir,

            # Ejecutar / Pausar / Detener
            "run": self._ui_run,
            "pause": self._ui_pause,
            "stop": self._ui_stop,

            # Tema
            "toggle_theme": self.toggle_theme,
        })

        # ===== MENÚ =====
        self.root.config(menu=IDEMenu(self.root, actions).build())

        # ===== TOOLBAR =====
        self.toolbar = Toolbar(self.top_container, actions)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        # ===== TEMA INICIAL =====
        self.apply_theme_to_widgets()
        self._update_title()

        # ===== FORZAR ACTUALIZACIÓN DEL STATUS =====
        self.root.after(50, self._update_cursor_status)

    # ====================================================
    # =================== THEME ==========================
    # ====================================================

    def toggle_theme(self):
        self.theme_mode = "light" if self.theme_mode == "dark" else "dark"
        self.apply_theme_callback(self.theme_mode)
        self.apply_theme_to_widgets()
        self._redraw_line_numbers()
        self._update_cursor_status()

    def apply_theme_to_widgets(self):
        t = self.THEMES[self.theme_mode]

        self.text_area.configure(
            bg=t["text_bg"],
            fg=t["text_fg"],
            insertbackground=t["cursor"],
            selectbackground=t["select_bg"],
        )

        self.line_numbers.configure(background=t["panel_bg"])

        if hasattr(self.panels, "apply_text_theme"):
            self.panels.apply_text_theme(
                bg=t["text_bg"],
                fg=t["text_fg"],
                cursor=t["cursor"],
                select_bg=t["select_bg"]
            )

    # ====================================================
    # =================== EDITOR =========================
    # ====================================================

    def _build_editor(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True)

        self.line_numbers = tk.Canvas(frame, width=50, highlightthickness=0)
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        scroll = ttk.Scrollbar(frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_area = tk.Text(
            frame,
            wrap="none",
            undo=True,
            yscrollcommand=scroll.set,
            relief="flat",
            borderwidth=0
        )

        try:
            self.text_area.configure(font=("Consolas", 11))
        except Exception:
            pass

        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=self._on_scroll)

        # Eventos para mantener status actualizado
        self.text_area.bind("<<Modified>>", self._on_modified)
        self.text_area.bind("<KeyRelease>", self._on_cursor_move)
        self.text_area.bind("<KeyPress>", self._on_cursor_move)
        self.text_area.bind("<Button-1>", self._on_cursor_move)
        self.text_area.bind("<ButtonRelease-1>", self._on_cursor_move)
        self.text_area.bind("<MouseWheel>", self._on_mousewheel)
        self.text_area.bind("<Configure>", lambda e: self._redraw_line_numbers())

        self._redraw_line_numbers()
        self._update_cursor_status()

    def _on_scroll(self, *args):
        self.text_area.yview(*args)
        self._redraw_line_numbers()
        self._update_cursor_status()

    def _on_mousewheel(self, event):
        self._redraw_line_numbers()
        self._update_cursor_status()

    def _on_modified(self, event=None):
        if self.text_area.edit_modified():
            self.state.is_dirty = True
            self.text_area.edit_modified(False)
            self._update_title()
            self._redraw_line_numbers()
            self._update_cursor_status()

    def _on_cursor_move(self, event=None):
        self._update_cursor_status()
        self._redraw_line_numbers()

    def _update_cursor_status(self):
        try:
            pos = self.text_area.index(tk.INSERT)
            line, col = pos.split(".")
            self.status.config(text=f"Ln {line}, Col {int(col) + 1}")
        except Exception:
            self.status.config(text="Ln 1, Col 1")

    def _redraw_line_numbers(self):
        self.line_numbers.delete("all")

        t = self.THEMES[self.theme_mode]
        line_color = t["line_fg"]

        f = font.Font(font=self.text_area["font"])
        _ = f.metrics("linespace")

        first = int(self.text_area.index("@0,0").split(".")[0])
        last = int(self.text_area.index(f"@0,{self.text_area.winfo_height()}").split(".")[0])

        for line in range(first, last + 1):
            dline = self.text_area.dlineinfo(f"{line}.0")
            if dline:
                y = dline[1]
                self.line_numbers.create_text(
                    46, y, anchor="ne", text=str(line), fill=line_color
                )

    # ====================================================
    # ============== FILE CALLBACKS ======================
    # ====================================================

    def _after_file_change(self, status: str):
        self._update_title()
        self._redraw_line_numbers()
        self._update_cursor_status()

    def _update_title(self):
        name = self.state.current_file if self.state.current_file else "Nuevo Archivo"
        star = "*" if self.state.is_dirty else ""
        self.root.title(f"IDE - {name}{star}")

    # ====================================================
    # ============== EXPLORADOR EVENTS ===================
    # ====================================================

    def _on_tree_open(self, event=None):
        item = self.panels.project_tree.focus()
        if not item:
            return

        values = self.panels.project_tree.item(item, "values")
        if not values:
            return

        path = values[0]
        if path and os.path.isfile(path):
            self.file_manager.open_file_path(path)

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

    def _ui_pause(self):
        self.panels.bottom_pane.select(3)
        self.panels.set_text(self.panels.exec_out, "⏸ Pausa (placeholder)\n")

    def _ui_stop(self):
        self.panels.bottom_pane.select(3)
        self.panels.set_text(self.panels.exec_out, "⏹ Detener (placeholder)\n")