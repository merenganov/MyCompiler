from enum import Enum, auto


class TokenType(Enum):
    # =========================
    # Identificadores y literales
    # =========================
    IDENTIFIER = auto()
    INTEGER = auto()
    REAL = auto()
    STRING = auto()
    CHAR = auto()

    # =========================
    # Palabras reservadas
    # =========================
    INT = auto()
    FLOAT = auto()
    REAL_TYPE = auto()   # para "real" (evita conflicto con REAL número)

    IF = auto()
    ELSE = auto()
    THEN = auto()
    END = auto()

    DO = auto()
    WHILE = auto()
    UNTIL = auto()

    CIN = auto()
    COUT = auto()

    MAIN = auto()

    # =========================
    # Operadores aritméticos
    # =========================
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    MODULO = auto()

    # =========================
    # Operadores relacionales
    # =========================
    ASSIGN = auto()        # =
    EQUAL = auto()         # ==
    NOT_EQUAL = auto()     # !=
    LESS = auto()          # <
    LESS_EQUAL = auto()    # <=
    GREATER = auto()       # >
    GREATER_EQUAL = auto() # >=

    # =========================
    # Operadores lógicos
    # =========================
    AND = auto()           # &&
    OR = auto()            # ||
    NOT = auto()           # !

    # =========================
    # Delimitadores
    # =========================
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    SEMICOLON = auto()
    COMMA = auto()
    DOT = auto()

    # =========================
    # Fin de archivo
    # =========================
    EOF = auto()


# =========================
# Palabras reservadas
# =========================
RESERVED_WORDS = {
    # Tipos
    "int": TokenType.INT,
    "float": TokenType.FLOAT,
    "real": TokenType.REAL_TYPE,

    # Control
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "then": TokenType.THEN,
    "end": TokenType.END,
    "do": TokenType.DO,
    "while": TokenType.WHILE,
    "until": TokenType.UNTIL,

    # Entrada / salida
    "cin": TokenType.CIN,
    "cout": TokenType.COUT,

    # Programa
    "main": TokenType.MAIN,
}