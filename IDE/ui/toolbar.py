import tkinter as tk
from tkinter import ttk


class Toolbar(ttk.Frame):
    """
    Toolbar con 'iconos' (Unicode) estilo IDE.
    Requiere actions:
      - run, pause, stop (pueden ser placeholders)
      - toggle_theme
      - (opcional) new, open, save
      - compile_lex, compile_syn, compile_sem, compile_ir
    """

    def __init__(self, parent, actions: dict):
        super().__init__(parent)
        self.actions = actions

        # =======================
        # Archivo
        # =======================
        self._icon_btn("📄", "new", tooltip="Nuevo")
        self._icon_btn("📂", "open", tooltip="Abrir")
        self._icon_btn("💾", "save", tooltip="Guardar")

        self._sep()

        # =======================
        # Compilación (NUEVO)
        # =======================
        self._text_btn_left("Léxico", "compile_lex", tooltip="Análisis Léxico")
        self._text_btn_left("Sintáctico", "compile_syn", tooltip="Análisis Sintáctico")
        self._text_btn_left("Semántico", "compile_sem", tooltip="Análisis Semántico")
        self._text_btn_left("Intermedio", "compile_ir", tooltip="Código Intermedio")

        self._sep()

        # =======================
        # Ejecutar / Pausar / Detener
        # =======================
        self._icon_btn("▶", "run", tooltip="Ejecutar")
        self._icon_btn("⏸", "pause", tooltip="Pausar")
        self._icon_btn("⏹", "stop", tooltip="Detener")

        self._sep()

        # Tema (derecha)
        self._spacer()
        self._text_btn("Oscuro/Claro", "toggle_theme")

    def _sep(self):
        ttk.Separator(self, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=4)

    def _spacer(self):
        ttk.Frame(self).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _icon_btn(self, icon: str, key: str, tooltip: str = ""):
        cmd = self.actions.get(key)
        state = tk.NORMAL if callable(cmd) else tk.DISABLED

        b = ttk.Button(self, text=icon, width=3, command=cmd, state=state)
        b.pack(side=tk.LEFT, padx=2, pady=2)

        if tooltip:
            self._add_tooltip(b, tooltip)

    def _text_btn(self, text: str, key: str):
        cmd = self.actions.get(key)
        state = tk.NORMAL if callable(cmd) else tk.DISABLED
        ttk.Button(self, text=text, command=cmd, state=state).pack(side=tk.RIGHT, padx=6, pady=2)

    # ✅ NUEVO: botón de texto alineado a la izquierda (sin afectar el botón de la derecha)
    def _text_btn_left(self, text: str, key: str, tooltip: str = ""):
        cmd = self.actions.get(key)
        state = tk.NORMAL if callable(cmd) else tk.DISABLED

        b = ttk.Button(self, text=text, command=cmd, state=state)
        b.pack(side=tk.LEFT, padx=2, pady=2)

        if tooltip:
            self._add_tooltip(b, tooltip)

    # Tooltip simple
    def _add_tooltip(self, widget, text: str):
        tip = {"win": None}

        def show(_):
            if tip["win"] is not None:
                return
            x = widget.winfo_rootx() + 20
            y = widget.winfo_rooty() + widget.winfo_height() + 5
            win = tk.Toplevel(widget)
            win.wm_overrideredirect(True)
            win.wm_geometry(f"+{x}+{y}")
            lbl = tk.Label(win, text=text, bg="#222", fg="#fff", padx=6, pady=3)
            lbl.pack()
            tip["win"] = win

        def hide(_):
            if tip["win"] is not None:
                tip["win"].destroy()
                tip["win"] = None

        widget.bind("<Enter>", show)
        widget.bind("<Leave>", hide)