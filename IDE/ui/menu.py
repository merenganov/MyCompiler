import tkinter as tk


class IDEMenu:
    def __init__(self, root, actions):
        """
        actions: dict con funciones:
          new, open, open_project, close, save, save_as, exit,
          compile_lex, compile_syn, compile_sem, compile_ir, run
        """
        self.root = root
        self.actions = actions

    def build(self):
        menubar = tk.Menu(self.root)

        # =====================================================
        # ==================== ARCHIVO ========================
        # =====================================================
        file_menu = tk.Menu(menubar, tearoff=0)

        file_menu.add_command(
            label="Nuevo",
            command=self.actions.get("new")
        )

        file_menu.add_command(
            label="Abrir Archivo...",
            command=self.actions.get("open")
        )

        # NUEVO: abrir proyecto/carpeta
        if "open_project" in self.actions:
            file_menu.add_command(
                label="Abrir Proyecto...",
                command=self.actions.get("open_project")
            )

        file_menu.add_command(
            label="Cerrar",
            command=self.actions.get("close")
        )

        file_menu.add_separator()

        file_menu.add_command(
            label="Guardar",
            command=self.actions.get("save")
        )

        file_menu.add_command(
            label="Guardar como...",
            command=self.actions.get("save_as")
        )

        file_menu.add_separator()

        file_menu.add_command(
            label="Salir",
            command=self.actions.get("exit")
        )

        menubar.add_cascade(label="Archivo", menu=file_menu)

        # =====================================================
        # ==================== COMPILAR =======================
        # =====================================================
        compile_menu = tk.Menu(menubar, tearoff=0)

        compile_menu.add_command(
            label="Análisis Léxico",
            command=self.actions.get("compile_lex")
        )

        compile_menu.add_command(
            label="Análisis Sintáctico",
            command=self.actions.get("compile_syn")
        )

        compile_menu.add_command(
            label="Análisis Semántico",
            command=self.actions.get("compile_sem")
        )

        compile_menu.add_command(
            label="Generar Código Intermedio",
            command=self.actions.get("compile_ir")
        )

        compile_menu.add_separator()

        compile_menu.add_command(
            label="Ejecutar",
            command=self.actions.get("run")
        )

        menubar.add_cascade(label="Compilar", menu=compile_menu)

        return menubar