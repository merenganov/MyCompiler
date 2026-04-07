class LexicalError(Exception):
    # Excepción especializada para errores detectados durante el análisis léxico.
    def __init__(self, message: str, line: int, column: int, character: str = "") -> None:
        self.message = message
        self.line = line
        self.column = column
        self.character = character

        if character:
            full_message = (
                f"Error léxico: {message}. "
                f"Línea {line}, columna {column}. "
                f"Carácter: {character!r}"
            )
        else:
            full_message = f"Error léxico: {message}. Línea {line}, columna {column}."

        super().__init__(full_message)