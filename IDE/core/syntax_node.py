# IDE/core/syntax_node.py

from copy import deepcopy
from core.token_type import TokenType


class SyntaxNode:
    def __init__(self, name, token=None):
        self.name = name
        self.token = token
        self.children = []

        # ======================================================
        # ANOTACIONES SEMÁNTICAS
        # ======================================================
        #
        # Estas anotaciones se utilizarán posteriormente
        # durante el análisis semántico.
        #
        # Persona 3 prepara la estructura.
        # Persona 2 será quien calcule y asigne los valores.
        #
        self.annotations = {
            "type": None,
            "value": None,
            "conversion": None
        }

    # ==========================================================
    # HIJOS
    # ==========================================================

    def add_child(self, child):
        if child is not None:
            self.children.append(child)

    def add_children(self, children):
        for child in children:
            self.add_child(child)

    def is_leaf(self):
        return len(self.children) == 0

    # ==========================================================
    # INFORMACIÓN DEL TOKEN
    # ==========================================================

    def get_token_value(self):
        if self.token is None:
            return None

        if hasattr(self.token, "lexeme"):
            return self.token.lexeme

        if hasattr(self.token, "value"):
            return self.token.value

        if hasattr(self.token, "literal"):
            return self.token.literal

        return str(self.token)

    def get_token_type(self):
        if self.token is None:
            return None

        if hasattr(self.token, "token_type"):
            return self.token.token_type

        if hasattr(self.token, "type"):
            return self.token.type

        return None

    def get_line(self):
        """
        Devuelve la línea asociada al token si está disponible.
        """

        if self.token is None:
            return None

        if hasattr(self.token, "line"):
            return self.token.line

        if hasattr(self.token, "line_number"):
            return self.token.line_number

        return None

    def get_column(self):
        """
        Devuelve la columna asociada al token si está disponible.
        """

        if self.token is None:
            return None

        if hasattr(self.token, "column"):
            return self.token.column

        if hasattr(self.token, "column_number"):
            return self.token.column_number

        return None

    # ==========================================================
    # ANOTACIONES SEMÁNTICAS
    # ==========================================================

    def set_annotation(self, key, value):
        """
        Asigna una anotación semántica al nodo.
        """

        self.annotations[key] = value

    def get_annotation(self, key):
        """
        Obtiene una anotación semántica.
        """

        return self.annotations.get(key)

    def clear_annotations(self):
        """
        Limpia las anotaciones semánticas del nodo.
        """

        self.annotations = {
            "type": None,
            "value": None,
            "conversion": None
        }

        for child in self.children:
            child.clear_annotations()

    # ==========================================================
    # COPIA DEL AST
    # ==========================================================

    def clone(self):
        """
        Genera una copia completa del nodo y sus hijos.

        Esto permite conservar el AST original y crear
        posteriormente un AST anotado independiente.
        """

        return deepcopy(self)

    # ==========================================================
    # REPRESENTACIÓN DEL AST ORIGINAL
    # ==========================================================

    def __str__(self):
        """
        Formato visual tipo AST:

        Operadores:
            +
            -
            =
            *

        Hojas:
            x <ID>
            23 <INT>
            24.0 <REAL>
        """

        token_value = self.get_token_value()
        token_type = self.get_token_type()

        if self.token is None:
            return self.name

        operator_types = {
            TokenType.PLUS,
            TokenType.MINUS,
            TokenType.STAR,
            TokenType.SLASH,
            TokenType.MODULO,
            TokenType.POWER,
            TokenType.ASSIGN,
            TokenType.EQUAL,
            TokenType.NOT_EQUAL,
            TokenType.LESS,
            TokenType.LESS_EQUAL,
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.AND,
            TokenType.OR,
            TokenType.NOT,
            TokenType.INCREMENT,
            TokenType.DECREMENT,
        }

        if token_type in operator_types:
            return str(token_value)

        if token_type == TokenType.IDENTIFIER:
            return f"{token_value} <ID>"

        if token_type == TokenType.INTEGER:
            return f"{token_value} <INT>"

        if token_type == TokenType.REAL:
            return f"{token_value} <REAL>"

        if token_type == TokenType.STRING:
            return f"{token_value} <STRING>"

        if token_type == TokenType.CHAR:
            return f"{token_value} <CHAR>"

        if self.name == "DECLARAR":
            return f"DECLARAR <{token_value}>"

        return f"{self.name}: {token_value}"

    # ==========================================================
    # REPRESENTACIÓN DEL AST ANOTADO
    # ==========================================================

    def semantic_str(self):
        """
        Representación textual del nodo incluyendo
        anotaciones semánticas.
        """

        base = str(self)

        semantic_type = self.annotations.get("type")
        semantic_value = self.annotations.get("value")
        conversion = self.annotations.get("conversion")

        annotations = []

        if semantic_type is not None:
            annotations.append(f"type={semantic_type}")

        if semantic_value is not None:
            annotations.append(f"value={semantic_value}")

        if conversion is not None:
            annotations.append(f"conversion={conversion}")

        if not annotations:
            return base

        return f"{base} [{', '.join(annotations)}]"

    # ==========================================================
    # CONVERSIÓN A DICCIONARIO
    # ==========================================================

    def to_dict(self):
        """
        AST original sin anotaciones semánticas.
        """

        return {
            "name": self.name,
            "token": self.get_token_value(),
            "line": self.get_line(),
            "column": self.get_column(),
            "children": [
                child.to_dict()
                for child in self.children
            ]
        }

    def to_semantic_dict(self):
        """
        AST con información semántica.
        """

        return {
            "name": self.name,
            "token": self.get_token_value(),
            "line": self.get_line(),
            "column": self.get_column(),
            "annotations": self.annotations.copy(),
            "children": [
                child.to_semantic_dict()
                for child in self.children
            ]
        }

    # ==========================================================
    # REPRESENTACIÓN TEXTUAL
    # ==========================================================

    def to_text(self, level=0):
        """
        Representación textual del AST original.
        """

        indentation = "  " * level
        result = f"{indentation}{str(self)}\n"

        for child in self.children:
            result += child.to_text(level + 1)

        return result

    def to_semantic_text(self, level=0):
        """
        Representación textual del AST anotado.
        """

        indentation = "  " * level
        result = f"{indentation}{self.semantic_str()}\n"

        for child in self.children:
            result += child.to_semantic_text(level + 1)

        return result


# ==============================================================
# FUNCIONES AUXILIARES
# ==============================================================

def tree_to_text(root_node):
    """
    Convierte el AST original a texto.
    """

    if root_node is None:
        return ""

    return root_node.to_text()


def semantic_tree_to_text(root_node):
    """
    Convierte el AST anotado a texto.
    """

    if root_node is None:
        return ""

    return root_node.to_semantic_text()


def clone_tree(root_node):
    """
    Crea una copia independiente del AST.
    """

    if root_node is None:
        return None

    return root_node.clone()