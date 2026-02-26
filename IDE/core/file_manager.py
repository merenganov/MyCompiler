from __future__ import annotations

import os
from tkinter import filedialog, messagebox

from .state import IDEState


class FileManager:
    def __init__(self, state: IDEState, editor_text_widget, root, on_after_change):
        """
        editor_text_widget: widget Text del editor
        root: ventana principal
        on_after_change: callback para refrescar UI (título, status, etc.)
        """
        self.state = state
        self.editor = editor_text_widget
        self.root = root
        self.on_after_change = on_after_change

    # ====================================================
    # ============== Helpers / Confirmaciones ============
    # ====================================================

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

    def _set_editor_content(self, content: str):
        self.editor.delete("1.0", "end")
        self.editor.insert("end", content)

    # ====================================================
    # =================== Archivo ========================
    # ====================================================

    def new_file(self):
        if not self.confirm_discard_or_save():
            return
        self._set_editor_content("")
        self.state.current_file = None
        self.state.is_dirty = False
        self.on_after_change(status="Nuevo archivo")

    def close_file(self):
        if not self.confirm_discard_or_save():
            return
        self._set_editor_content("")
        self.state.current_file = None
        self.state.is_dirty = False
        self.on_after_change(status="Archivo cerrado")

    def open_file(self):
        if not self.confirm_discard_or_save():
            return

        path = filedialog.askopenfilename(
            title="Abrir archivo",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        if not path:
            return

        self.open_file_path(path)

    def open_file_path(self, path: str):
        """Abre un archivo por ruta (usado por el explorador)."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            self._set_editor_content(content)
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
            title="Guardar como",
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

    # ====================================================
    # ================= Proyecto (Treeview) ==============
    # ====================================================

    def open_project_folder(self, treeview):
        """
        Selecciona una carpeta y la carga en el TreeView.
        Cada nodo guarda su ruta en values=(full_path,).
        IDEWindow abre con open_file_path() cuando es archivo.
        """
        folder = filedialog.askdirectory(title="Selecciona una carpeta de proyecto")
        if not folder:
            return

        # Limpiar tree
        for item in treeview.get_children():
            treeview.delete(item)

        root_node = treeview.insert(
            "",
            "end",
            text=os.path.basename(folder) or folder,
            values=(folder,),
            open=True
        )

        ignore = {"__pycache__", ".git", ".venv", "venv", "node_modules"}

        def insert_nodes(parent_id, parent_path):
            try:
                entries = sorted(os.listdir(parent_path))
            except Exception:
                return

            for name in entries:
                if name in ignore:
                    continue

                full = os.path.join(parent_path, name)

                # Insertar nodo
                node_id = treeview.insert(
                    parent_id,
                    "end",
                    text=name,
                    values=(full,)
                )

                # Si es carpeta, cargar hijos
                if os.path.isdir(full):
                    insert_nodes(node_id, full)

        insert_nodes(root_node, folder)

        self.on_after_change(status=f"Proyecto abierto: {folder}")