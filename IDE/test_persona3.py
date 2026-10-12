import tkinter as tk

from ui.ide_window import IDEWindow
from core.syntax_node import SyntaxNode


# ==========================================================
# VENTANA
# ==========================================================

root = tk.Tk()


def apply_theme(theme):
    pass


ide = IDEWindow(
    root,
    apply_theme_callback=apply_theme,
    default_theme="dark"
)


# ==========================================================
# MOCK - TABLA DE SÍMBOLOS
# ==========================================================

mock_symbols = [
    {
        "name": "x",
        "data_type": "int",
        "lines": [4, 7, 8, 13],
        "address": 0,
        "scope": "global",
        "value": None
    },
    {
        "name": "y",
        "data_type": "int",
        "lines": [4, 9, 10, 11],
        "address": 1,
        "scope": "global",
        "value": None
    },
    {
        "name": "a",
        "data_type": "real",
        "lines": [5, 12, 18],
        "address": 2,
        "scope": "global",
        "value": None
    },
    {
        "name": "temporal",
        "data_type": "int",
        "lines": [20],
        "address": 3,
        "scope": "if_1",
        "value": None
    }
]

ide._set_symbol_table_output(mock_symbols)


# ==========================================================
# MOCK - ERRORES SEMÁNTICOS
# ==========================================================

mock_errors = (
    "Línea 6, Columna 1: Identificador 'suma' no declarado\n"
    "Línea 20, Columna 1: Identificador 'x' ya declarado\n"
    "Línea 7, Columna 3: Incompatibilidad de tipos int <- real\n"
)

ide._set_semantic_error_output(mock_errors)


# ==========================================================
# MOCK - AST ANOTADO
# ==========================================================

root_node = SyntaxNode("+")
left = SyntaxNode("x")
right = SyntaxNode("5")

root_node.add_child(left)
root_node.add_child(right)

root_node.set_annotation("type", "float")

left.set_annotation(
    "type",
    "float"
)

right.set_annotation(
    "type",
    "int"
)

right.set_annotation(
    "value",
    5
)

right.set_annotation(
    "conversion",
    "int -> float"
)


# ==========================================================
# ABRIR AST SEMÁNTICO
# ==========================================================

root.after(
    500,
    lambda: ide._open_semantic_tree_window(root_node)
)


# Seleccionar pestaña Símbolos para verla inmediatamente.
root.after(
    200,
    lambda: ide.panels.results_notebook.select(4)
)


root.mainloop()