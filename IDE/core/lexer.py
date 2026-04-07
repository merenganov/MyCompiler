from typing import List, Optional

from core.lexical_error import LexicalError
from core.token_model import Token
from core.token_type import RESERVED_WORDS, TokenType


class Lexer:
    # Analizador léxico basado en recorrido carácter por carácter.
    def __init__(self, source: str) -> None:
        self.source = source if source is not None else ""
        self.position = 0
        self.line = 1
        self.column = 1

    def current_char(self) -> Optional[str]:
        # Devuelve el carácter actual o None si se alcanzó el final.
        if self.position >= len(self.source):
            return None
        return self.source[self.position]

    def peek(self, offset: int = 1) -> Optional[str]:
        # Devuelve un carácter futuro sin mover la posición actual.
        index = self.position + offset
        if index >= len(self.source):
            return None
        return self.source[index]

    def advance(self) -> None:
        # Avanza una posición y actualiza línea y columna.
        current = self.current_char()
        if current is None:
            return

        self.position += 1

        if current == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1

    def tokenize(self) -> List[Token]:
        # Recorre toda la entrada y devuelve la lista de tokens.
        tokens: List[Token] = []

        while self.current_char() is not None:
            self.skip_ignored()

            if self.current_char() is None:
                break

            current = self.current_char()

            if current.isalpha() or current == "_":
                tokens.append(self.scan_identifier_or_keyword())
                continue

            if current.isdigit():
                tokens.append(self.scan_number())
                continue

            tokens.append(self.scan_operator_or_delimiter())

        tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return tokens

    def skip_ignored(self) -> None:
        # Omite espacios en blanco y comentarios de una línea con //.
        while True:
            current = self.current_char()

            while current is not None and current.isspace():
                self.advance()
                current = self.current_char()

            if current == "/" and self.peek() == "/":
                while self.current_char() not in (None, "\n"):
                    self.advance()
                continue

            break

    def scan_identifier_or_keyword(self) -> Token:
        # Reconoce identificadores y palabras reservadas.
        start_line = self.line
        start_column = self.column
        lexeme_chars = []

        while True:
            current = self.current_char()
            if current is None or not (current.isalnum() or current == "_"):
                break

            lexeme_chars.append(current)
            self.advance()

        lexeme = "".join(lexeme_chars)
        token_type = RESERVED_WORDS.get(lexeme, TokenType.IDENTIFIER)

        return Token(token_type, lexeme, start_line, start_column)

    def scan_number(self) -> Token:
        # Reconoce enteros y reales simples.
        start_line = self.line
        start_column = self.column
        lexeme_chars = []

        while self.current_char() is not None and self.current_char().isdigit():
            lexeme_chars.append(self.current_char())
            self.advance()

        if self.current_char() == "." and self.peek() is not None and self.peek().isdigit():
            lexeme_chars.append(".")
            self.advance()

            while self.current_char() is not None and self.current_char().isdigit():
                lexeme_chars.append(self.current_char())
                self.advance()

            return Token(TokenType.REAL, "".join(lexeme_chars), start_line, start_column)

        return Token(TokenType.INTEGER, "".join(lexeme_chars), start_line, start_column)

    def scan_operator_or_delimiter(self) -> Token:
        # Reconoce operadores de uno y dos caracteres, además de delimitadores.
        start_line = self.line
        start_column = self.column
        current = self.current_char()

        if current is None:
            return Token(TokenType.EOF, "", start_line, start_column)

        two_char_tokens = {
            "==": TokenType.EQUAL,
            "!=": TokenType.NOT_EQUAL,
            "<=": TokenType.LESS_EQUAL,
            ">=": TokenType.GREATER_EQUAL,
        }

        pair = current + (self.peek() or "")
        if pair in two_char_tokens:
            self.advance()
            self.advance()
            return Token(two_char_tokens[pair], pair, start_line, start_column)

        one_char_tokens = {
            "+": TokenType.PLUS,
            "-": TokenType.MINUS,
            "*": TokenType.STAR,
            "/": TokenType.SLASH,
            "=": TokenType.ASSIGN,
            "<": TokenType.LESS,
            ">": TokenType.GREATER,
            "(": TokenType.LPAREN,
            ")": TokenType.RPAREN,
            "{": TokenType.LBRACE,
            "}": TokenType.RBRACE,
            "[": TokenType.LBRACKET,
            "]": TokenType.RBRACKET,
            ";": TokenType.SEMICOLON,
            ",": TokenType.COMMA,
            ".": TokenType.DOT,
        }

        if current in one_char_tokens:
            self.advance()
            return Token(one_char_tokens[current], current, start_line, start_column)

        raise LexicalError(
            message="Símbolo no reconocido",
            line=start_line,
            column=start_column,
            character=current,
        )