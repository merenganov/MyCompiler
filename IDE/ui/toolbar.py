import tkinter as tk
from tkinter import ttk

class Toolbar:
    def __init__(self, parent, actions):
        self.frame = ttk.Frame(parent)
        self.actions = actions

        ttk.Button(self.frame, text="Léxico", command=actions["compile_lex"]).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.frame, text="Sintáctico", command=actions["compile_syn"]).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.frame, text="Semántico", command=actions["compile_sem"]).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.frame, text="Intermedio", command=actions["compile_ir"]).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.frame, text="Ejecutar", command=actions["run"]).pack(side=tk.LEFT, padx=2)

    def pack(self):
        self.frame.pack(fill=tk.X, padx=6, pady=4)