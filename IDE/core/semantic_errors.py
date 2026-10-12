class SemanticError:
    """
    Representa un error detectado durante el análisis semántico.
    """

    def __init__(
        self,
        error_type,
        message,
        line=None,
        column=None
    ):
        self.error_type = error_type
        self.message = message
        self.line = line
        self.column = column

    def to_dict(self):
        """
        Convierte el error a diccionario para facilitar
        su visualización posterior en el IDE.
        """

        return {
            "error_type": self.error_type,
            "message": self.message,
            "line": self.line,
            "column": self.column
        }

    def __str__(self):
        """
        Representación legible del error.
        """

        location = ""

        if self.line is not None:
            location += f"Línea {self.line}"

        if self.column is not None:
            if location:
                location += ", "
            location += f"Columna {self.column}"

        if location:
            return f"[{self.error_type}] {location}: {self.message}"

        return f"[{self.error_type}] {self.message}"


class SemanticErrorManager:
    """
    Administra todos los errores semánticos detectados
    durante el análisis.
    """

    def __init__(self):
        self.errors = []

    # ==========================================================
    # REGISTRO GENERAL
    # ==========================================================

    def add_error(
        self,
        error_type,
        message,
        line=None,
        column=None
    ):
        """
        Registra un nuevo error semántico.
        """

        error = SemanticError(
            error_type=error_type,
            message=message,
            line=line,
            column=column
        )

        self.errors.append(error)

        return error

    # ==========================================================
    # IDENTIFICADORES
    # ==========================================================

    def undeclared_identifier(
        self,
        name,
        line=None,
        column=None
    ):
        """
        Error por uso de una variable o identificador
        no declarado.
        """

        return self.add_error(
            error_type="undeclared_identifier",
            message=f"Identificador '{name}' no declarado",
            line=line,
            column=column
        )

    def duplicate_identifier(
        self,
        name,
        scope=None,
        line=None,
        column=None
    ):
        """
        Error por declaración duplicada.
        """

        if scope:
            message = (
                f"Identificador '{name}' ya declarado "
                f"en el ámbito '{scope}'"
            )
        else:
            message = (
                f"Identificador '{name}' ya declarado"
            )

        return self.add_error(
            error_type="duplicate_identifier",
            message=message,
            line=line,
            column=column
        )

    # ==========================================================
    # TIPOS
    # ==========================================================

    def type_mismatch(
        self,
        expected_type,
        received_type,
        line=None,
        column=None
    ):
        """
        Error por incompatibilidad de tipos.
        """

        return self.add_error(
            error_type="type_mismatch",
            message=(
                f"Se esperaba un valor de tipo "
                f"'{expected_type}', pero se recibió "
                f"'{received_type}'"
            ),
            line=line,
            column=column
        )

    def invalid_conversion(
        self,
        source_type,
        target_type,
        line=None,
        column=None
    ):
        """
        Error por conversión de tipos no válida.
        """

        return self.add_error(
            error_type="invalid_conversion",
            message=(
                f"No se puede convertir el tipo "
                f"'{source_type}' a '{target_type}'"
            ),
            line=line,
            column=column
        )

    # ==========================================================
    # OPERADORES
    # ==========================================================

    def invalid_operator(
        self,
        operator,
        left_type=None,
        right_type=None,
        line=None,
        column=None
    ):
        """
        Error por uso indebido de un operador.
        """

        if right_type is not None:
            message = (
                f"El operador '{operator}' no es válido "
                f"para operandos de tipo "
                f"'{left_type}' y '{right_type}'"
            )
        else:
            message = (
                f"El operador '{operator}' no es válido "
                f"para un operando de tipo '{left_type}'"
            )

        return self.add_error(
            error_type="invalid_operator",
            message=message,
            line=line,
            column=column
        )

    # ==========================================================
    # CONDICIONES
    # ==========================================================

    def invalid_condition(
        self,
        received_type,
        line=None,
        column=None
    ):
        """
        Error cuando una estructura de control requiere
        una expresión booleana y recibe otro tipo.
        """

        return self.add_error(
            error_type="invalid_condition",
            message=(
                f"La condición debe ser de tipo 'bool', "
                f"pero se recibió '{received_type}'"
            ),
            line=line,
            column=column
        )

    # ==========================================================
    # CONSULTA DE ERRORES
    # ==========================================================

    def has_errors(self):
        """
        Indica si existen errores semánticos.
        """

        return len(self.errors) > 0

    def get_all(self):
        """
        Devuelve todos los errores como diccionarios.
        """

        return [
            error.to_dict()
            for error in self.errors
        ]

    def get_objects(self):
        """
        Devuelve directamente los objetos SemanticError.
        """

        return self.errors.copy()

    def count(self):
        """
        Devuelve la cantidad de errores detectados.
        """

        return len(self.errors)

    # ==========================================================
    # LIMPIEZA
    # ==========================================================

    def clear(self):
        """
        Elimina todos los errores registrados.
        """

        self.errors.clear()