from __future__ import annotations
from tkinter import filedialog, messagebox
from .state import IDEState

class FileManager:
    def __init__(self, state: IDEState, editor_text_widget, root, on_after_change):
        """
        editor_text_widget: widget Text del editor
        root: ventana principal
        on_after_change: callback para refrescar UI (título, líneas, etc.)
        """
        self.state = state
        self.editor = editor_text_widget
        self.root = root
        self.on_after_change = on_after_change

    def confirm_discard_or_save(self) -> bool:
        """True si podemos continuar, False si el usuario canceló."""
        if not self.state.is_dirty:
            return True

        choice = messagebox.askyesnocancel(
            "Cambios sin guardar",
            "Tienes cambios sin guardar.\n¿Deseas guardarlos?"
        )
        if choice is None:
            return False
        if choice is True:
            return self.save()
        return True

    def new_file(self):
        if not self.confirm_discard_or_save():
            return
        self.editor.delete("1.0", "end")
        self.state.current_file = None
        self.state.is_dirty = False
        self.on_after_change(status="Nuevo archivo")

    def close_file(self):
        if not self.confirm_discard_or_save():
            return
        self.editor.delete("1.0", "end")
        self.state.current_file = None
        self.state.is_dirty = False
        self.on_after_change(status="Archivo cerrado")

    def open_file(self):
        if not self.confirm_discard_or_save():
            return

        path = filedialog.askopenfilename(
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.editor.delete("1.0", "end")
            self.editor.insert("end", content)
            self.state.current_file = path
            self.state.is_dirty = False
            self.on_after_change(status=f"Abierto: {path}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{e}")

    def save(self) -> bool:
        if self.state.current_file is None:
            return self.save_as()

        try:
            with open(self.state.current_file, "w", encoding="utf-8") as f:
                f.write(self.editor.get("1.0", "end-1c"))
            self.state.is_dirty = False
            self.on_after_change(status=f"Guardado: {self.state.current_file}")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar:\n{e}")
            return False

    def save_as(self) -> bool:
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        if not path:
            return False

        self.state.current_file = path
        return self.save()

    def exit_app(self):
        if not self.confirm_discard_or_save():
            return
        self.root.quit()