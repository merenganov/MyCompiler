class Symbol:
    """
    Representa un identificador almacenado en la tabla de símbolos.
    """

    def __init__(
        self,
        name,
        data_type,
        line=None,
        address=None,
        scope="global"
    ):
        self.name = name
        self.data_type = data_type

        # Líneas donde aparece el identificador.
        self.lines = []

        if line is not None:
            self.lines.append(line)

        # Dirección/desplazamiento dentro de la tabla.
        self.address = address

        # Ámbito al que pertenece.
        self.scope = scope

        # Valor conocido, si existe.
        self.value = None

    def add_line(self, line):
        """
        Registra una nueva línea donde fue utilizado
        el identificador.
        """

        if line is None:
            return

        if line not in self.lines:
            self.lines.append(line)

    def to_dict(self):
        """
        Convierte el símbolo a diccionario para facilitar
        su visualización posterior en el IDE.
        """

        return {
            "name": self.name,
            "data_type": self.data_type,
            "lines": self.lines.copy(),
            "address": self.address,
            "scope": self.scope,
            "value": self.value
        }


class SymbolTable:
    """
    Tabla de símbolos utilizada durante el análisis semántico.
    """

    def __init__(self):

        # ======================================================
        # PILA DE ÁMBITOS ACTIVOS
        # ======================================================

        # scopes[0] siempre representa el ámbito global.
        self.scopes = [
            {
                "name": "global",
                "symbols": {}
            }
        ]

        # ======================================================
        # HISTORIAL DE SÍMBOLOS
        # ======================================================

        # Conserva TODOS los símbolos declarados durante
        # el análisis, incluso cuando su ámbito ya terminó.
        #
        # Esto permite mostrar posteriormente la tabla completa
        # dentro del IDE.
        self.all_symbols = []

        # ======================================================
        # DIRECCIONES
        # ======================================================

        # Contador utilizado como dirección/desplazamiento lógico.
        self.next_address = 0

        # Contador para generar nombres únicos de ámbitos.
        self.scope_counter = 0

    # ==========================================================
    # ÁMBITOS
    # ==========================================================

    def current_scope(self):
        """
        Devuelve el nombre del ámbito actual.
        """

        return self.scopes[-1]["name"]

    def enter_scope(self, scope_name=None):
        """
        Crea y entra a un nuevo ámbito.
        """

        if scope_name is None:
            self.scope_counter += 1
            scope_name = f"scope_{self.scope_counter}"

        self.scopes.append(
            {
                "name": scope_name,
                "symbols": {}
            }
        )

        return scope_name

    def exit_scope(self):
        """
        Sale del ámbito actual.

        Los símbolos dejan de estar disponibles para
        lookup(), pero permanecen almacenados dentro
        del historial general.

        No permite eliminar el ámbito global.
        """

        if len(self.scopes) == 1:
            raise Exception(
                "No se puede salir del ámbito global"
            )

        return self.scopes.pop()

    # ==========================================================
    # INSERCIÓN / DECLARACIÓN
    # ==========================================================

    def insert(self, name, data_type, line=None):
        """
        Inserta un identificador en el ámbito actual.

        Retorna el símbolo creado.

        Si ya existe dentro del mismo ámbito,
        genera una excepción.
        """

        current = self.scopes[-1]
        symbols = current["symbols"]

        # La duplicidad solamente se comprueba
        # dentro del ámbito actual.
        if name in symbols:
            raise Exception(
                f"Variable '{name}' ya declarada "
                f"en el ámbito '{current['name']}'"
            )

        symbol = Symbol(
            name=name,
            data_type=data_type,
            line=line,
            address=self.next_address,
            scope=current["name"]
        )

        # Se agrega al ámbito activo.
        symbols[name] = symbol

        # También se almacena permanentemente
        # en el historial de la tabla.
        self.all_symbols.append(symbol)

        # Se incrementa el desplazamiento lógico.
        self.next_address += 1

        return symbol

    def declare(self, name, type_, line=None):
        """
        Se conserva este método por compatibilidad
        con el código anterior del compilador.

        Internamente utiliza insert().
        """

        return self.insert(
            name=name,
            data_type=type_,
            line=line
        )

    # ==========================================================
    # BÚSQUEDA
    # ==========================================================

    def lookup(self, name):
        """
        Busca un identificador desde el ámbito actual
        hacia los ámbitos superiores.

        Solo busca dentro de ámbitos actualmente activos.

        Retorna el símbolo si existe.
        Retorna None si no existe.
        """

        for scope in reversed(self.scopes):

            symbols = scope["symbols"]

            if name in symbols:
                return symbols[name]

        return None

    def exists(self, name, current_scope_only=False):
        """
        Comprueba si un identificador existe.

        current_scope_only=True:
            Solo revisa el ámbito actual.

        current_scope_only=False:
            Busca también en ámbitos superiores.
        """

        if current_scope_only:
            return name in self.scopes[-1]["symbols"]

        return self.lookup(name) is not None

    # ==========================================================
    # USOS DE IDENTIFICADORES
    # ==========================================================

    def add_usage(self, name, line):
        """
        Registra una línea donde fue utilizado
        un identificador.

        Retorna True si pudo registrarse.
        Retorna False si el identificador no existe.
        """

        symbol = self.lookup(name)

        if symbol is None:
            return False

        symbol.add_line(line)

        return True

    # ==========================================================
    # ASIGNACIÓN
    # ==========================================================

    def assign(self, name, value, line=None):
        """
        Asigna un valor a un identificador existente.

        Se mantiene este método para conservar
        compatibilidad con el código anterior.
        """

        symbol = self.lookup(name)

        if symbol is None:
            raise Exception(
                f"Variable '{name}' no declarada"
            )

        symbol.value = value

        if line is not None:
            symbol.add_line(line)

        return symbol

    # ==========================================================
    # OBTENCIÓN DE TIPO
    # ==========================================================

    def get_type(self, name):
        """
        Obtiene el tipo de un identificador.

        Retorna None si el identificador
        no está declarado.
        """

        symbol = self.lookup(name)

        if symbol is None:
            return None

        return symbol.data_type

    # ==========================================================
    # OBTENCIÓN DE INFORMACIÓN
    # ==========================================================

    def get_all(self):
        """
        Devuelve TODOS los símbolos encontrados durante
        el análisis.

        Incluye símbolos pertenecientes a ámbitos
        que ya fueron cerrados.

        Se devuelve como lista de diccionarios para
        facilitar su visualización posterior en el IDE.
        """

        return [
            symbol.to_dict()
            for symbol in self.all_symbols
        ]

    def get_active_symbols(self):
        """
        Devuelve únicamente los símbolos pertenecientes
        a ámbitos que actualmente siguen activos.
        """

        result = []

        for scope in self.scopes:

            for symbol in scope["symbols"].values():
                result.append(symbol.to_dict())

        return result

    def get_current_scope_symbols(self):
        """
        Devuelve los símbolos pertenecientes
        únicamente al ámbito actual.
        """

        return [
            symbol.to_dict()
            for symbol in self.scopes[-1]["symbols"].values()
        ]

    # ==========================================================
    # LIMPIEZA
    # ==========================================================

    def clear(self):
        """
        Reinicia completamente la tabla de símbolos.
        """

        self.scopes = [
            {
                "name": "global",
                "symbols": {}
            }
        ]

        self.all_symbols = []

        self.next_address = 0

        self.scope_counter = 0