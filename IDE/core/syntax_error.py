# IDE/core/syntax_error.py

class SyntaxErrorCompiler(Exception):
    """
    Error personalizado para el análisis sintáctico.
    Sirve para mostrar mensajes claros con línea, columna,
    token encontrado y token esperado.
    """

    def __init__(self, message, token=None, expected=None):
        self.message = message
        self.token = token
        self.expected = expected
        super().__init__(self.__str__())

    def __str__(self):
        if self.token is None:
            return f"Error sintáctico: {self.message}"

        line = getattr(self.token, "line", "?")
        column = getattr(self.token, "column", "?")
        lexeme = getattr(self.token, "lexeme", "")
        token_type = getattr(self.token, "token_type", None)

        if token_type is not None:
            found = token_type.name
        else:
            found = "DESCONOCIDO"

        expected_text = ""
        if self.expected is not None:
            expected_text = f" Se esperaba: {self.expected}."

        return (
            f"Error sintáctico en línea {line}, columna {column}: "
            f"{self.message}. Token encontrado: {found} '{lexeme}'."
            f"{expected_text}"
        )