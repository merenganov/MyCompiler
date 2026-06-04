# IDE/core/syntax_node.py

class SyntaxNode:
    """
    Representa un nodo del árbol sintáctico.

    Cada nodo puede tener:
    - name: nombre del nodo gramatical, por ejemplo PROGRAMA, DECLARACION, EXPRESION.
    - token: token asociado, por ejemplo un identificador, número, operador, etc.
    - children: lista de nodos hijos.
    """

    def __init__(self, name, token=None):
        self.name = name
        self.token = token
        self.children = []

    def add_child(self, child):
        """
        Agrega un nodo hijo al nodo actual.
        """
        if child is not None:
            self.children.append(child)

    def add_children(self, children):
        """
        Agrega varios hijos al nodo actual.
        """
        for child in children:
            self.add_child(child)

    def is_leaf(self):
        """
        Indica si el nodo no tiene hijos.
        """
        return len(self.children) == 0

    def get_token_value(self):
        """
        Obtiene el valor visible del token.

        Se intenta usar lexeme porque comúnmente los tokens tienen ese atributo.
        También se contemplan otros nombres por si tu Token usa value o literal.
        """
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
        """
        Obtiene el tipo del token, si existe.
        """
        if self.token is None:
            return None

        if hasattr(self.token, "type"):
            return self.token.type

        if hasattr(self.token, "token_type"):
            return self.token.token_type

        return None

    def __str__(self):
        """
        Representación del nodo para mostrarlo en consola o en el Treeview.
        """
        token_value = self.get_token_value()

        if token_value is not None:
            return f"{self.name}: {token_value}"

        return self.name

    def to_dict(self):
        """
        Convierte el árbol a diccionario.
        Puede servir después si quieres exportar el árbol como JSON.
        """
        return {
            "name": self.name,
            "token": self.get_token_value(),
            "children": [child.to_dict() for child in self.children]
        }

    def to_text(self, level=0):
        """
        Convierte el árbol sintáctico a texto con indentación.
        Útil para mostrarlo en consola o guardarlo en outputs/syntax_tree.txt.
        """
        indentation = "  " * level
        result = f"{indentation}{str(self)}\n"

        for child in self.children:
            result += child.to_text(level + 1)

        return result


def tree_to_text(root_node):
    """
    Función auxiliar para convertir el árbol completo a texto.
    """
    if root_node is None:
        return ""

    return root_node.to_text()