# IDE/core/syntax_node.py

from core.token_type import TokenType


class SyntaxNode:
    def __init__(self, name, token=None):
        self.name = name
        self.token = token
        self.children = []

    def add_child(self, child):
        if child is not None:
            self.children.append(child)

    def add_children(self, children):
        for child in children:
            self.add_child(child)

    def is_leaf(self):
        return len(self.children) == 0

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

        # Operadores como raíz: +, -, *, /, =, >, ==, &&
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

        # Identificadores y literales como en la imagen
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

        # Declaraciones
        if self.name == "DECLARAR":
            return f"DECLARAR <{token_value}>"

        return f"{self.name}: {token_value}"

    def to_dict(self):
        return {
            "name": self.name,
            "token": self.get_token_value(),
            "children": [child.to_dict() for child in self.children]
        }

    def to_text(self, level=0):
        indentation = "  " * level
        result = f"{indentation}{str(self)}\n"

        for child in self.children:
            result += child.to_text(level + 1)

        return result


def tree_to_text(root_node):
    if root_node is None:
        return ""

    return root_node.to_text()