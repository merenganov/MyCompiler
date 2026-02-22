import tkinter as tk

class IDEMenu:
    def __init__(self, root, actions):
        """
        actions: dict con funciones:
          new, open, close, save, save_as, exit,
          compile_lex, compile_syn, compile_sem, compile_ir, run
        """
        self.root = root
        self.actions = actions

    def build(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Nuevo", command=self.actions["new"])
        file_menu.add_command(label="Abrir", command=self.actions["open"])
        file_menu.add_command(label="Cerrar", command=self.actions["close"])
        file_menu.add_separator()
        file_menu.add_command(label="Guardar", command=self.actions["save"])
        file_menu.add_command(label="Guardar como", command=self.actions["save_as"])
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.actions["exit"])
        menubar.add_cascade(label="Archivo", menu=file_menu)

        compile_menu = tk.Menu(menubar, tearoff=0)
        compile_menu.add_command(label="Análisis Léxico", command=self.actions["compile_lex"])
        compile_menu.add_command(label="Análisis Sintáctico", command=self.actions["compile_syn"])
        compile_menu.add_command(label="Análisis Semántico", command=self.actions["compile_sem"])
        compile_menu.add_command(label="Código Intermedio", command=self.actions["compile_ir"])
        compile_menu.add_separator()
        compile_menu.add_command(label="Ejecución", command=self.actions["run"])
        menubar.add_cascade(label="Compilar", menu=compile_menu)

        return menubar