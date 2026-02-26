import tkinter as tk


class IDEMenu:
    def __init__(self, root, actions: dict):
        self.root = root
        self.actions = actions

    def _cmd(self, key: str):
        # Devuelve una función válida aunque falte la acción
        fn = self.actions.get(key)
        return fn if callable(fn) else (lambda: None)

    def build(self):
        menubar = tk.Menu(self.root)

        # ===== Archivo =====
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Nuevo", command=self._cmd("new"))
        file_menu.add_command(label="Abrir Archivo...", command=self._cmd("open"))
        file_menu.add_command(label="Abrir Proyecto...", command=self._cmd("open_project"))
        file_menu.add_command(label="Cerrar", command=self._cmd("close"))
        file_menu.add_separator()
        file_menu.add_command(label="Guardar", command=self._cmd("save"))
        file_menu.add_command(label="Guardar como...", command=self._cmd("save_as"))
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self._cmd("exit"))
        menubar.add_cascade(label="Archivo", menu=file_menu)

        # ===== Compilar =====
        compile_menu = tk.Menu(menubar, tearoff=0)
        compile_menu.add_command(label="Análisis Léxico", command=self._cmd("compile_lex"))
        compile_menu.add_command(label="Análisis Sintáctico", command=self._cmd("compile_syn"))
        compile_menu.add_command(label="Análisis Semántico", command=self._cmd("compile_sem"))
        compile_menu.add_command(label="Código Intermedio", command=self._cmd("compile_ir"))
        compile_menu.add_separator()
        compile_menu.add_command(label="Ejecutar", command=self._cmd("run"))
        compile_menu.add_command(label="Pausar", command=self._cmd("pause"))
        compile_menu.add_command(label="Detener", command=self._cmd("stop"))
        menubar.add_cascade(label="Compilar", menu=compile_menu)

        return menubar