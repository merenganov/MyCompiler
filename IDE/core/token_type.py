from enum import Enum, auto


class TokenType(Enum):
    # Identificadores y literales numéricos.
    IDENTIFIER = auto()
    INTEGER = auto()
    REAL = auto()

    # Palabras reservadas.
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    RETURN = auto()
    FUNCTION = auto()
    VAR = auto()
    TRUE = auto()
    FALSE = auto()
    PRINT = auto()

    # Operadores.
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    ASSIGN = auto()
    EQUAL = auto()
    NOT_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()

    # Delimitadores.
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    SEMICOLON = auto()
    COMMA = auto()
    DOT = auto()

    # Fin de archivo.
    EOF = auto()


# Mapa de palabras reservadas del lenguaje.
RESERVED_WORDS = {
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "for": TokenType.FOR,
    "return": TokenType.RETURN,
    "function": TokenType.FUNCTION,
    "var": TokenType.VAR,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "print": TokenType.PRINT,
}