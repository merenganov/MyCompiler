import tkinter as tk
from tkinter import ttk


class Toolbar(ttk.Frame):
    def __init__(self, parent, actions: dict):
        super().__init__(parent)
        self.actions = actions

        # Solo botón de tema
        cmd = self.actions.get("toggle_theme")
        state = tk.NORMAL if callable(cmd) else tk.DISABLED
        ttk.Button(self, text="Oscuro/Claro", command=cmd, state=state).pack(
            side=tk.RIGHT, padx=6, pady=2
        )