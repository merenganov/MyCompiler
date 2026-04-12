from typing import List, Optional, Tuple

from core.lexical_error import LexicalError
from core.token_model import Token
from core.token_type import RESERVED_WORDS, TokenType


class Lexer:
    def __init__(self, source: str) -> None:
        self.source = source if source is not None else ""
        self.position = 0
        self.line = 1
        self.column = 1

    def current_char(self) -> Optional[str]:
        if self.position >= len(self.source):
            return None
        return self.source[self.position]

    def peek(self, offset: int = 1) -> Optional[str]:
        index = self.position + offset
        if index >= len(self.source):
            return None
        return self.source[index]

    def advance(self) -> None:
        current = self.current_char()
        if current is None:
            return

        self.position += 1

        if current == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1

    def tokenize(self) -> Tuple[List[Token], List[LexicalError]]:
        tokens: List[Token] = []
        errors: List[LexicalError] = []

        while self.current_char() is not None:
            start_position = self.position

            try:
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

                if current == '"':
                    tokens.append(self.scan_string())
                    continue

                if current == "'":
                    tokens.append(self.scan_char())
                    continue

                if current == "." and self.peek() is not None and self.peek().isdigit():
                    raise LexicalError(
                        message="Número mal formado",
                        line=self.line,
                        column=self.column,
                        character=".",
                    )

                tokens.append(self.scan_operator_or_delimiter())

            except LexicalError as error:
                errors.append(error)

                # Recuperación para no quedarse atorado en el mismo carácter
                if self.current_char() is None:
                    break

                if self.position == start_position:
                    self.advance()

                continue

        tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return tokens, errors

    def skip_ignored(self) -> None:
        while True:
            current = self.current_char()

            while current is not None and current.isspace():
                self.advance()
                current = self.current_char()

            if current == "/" and self.peek() == "/":
                self.advance()
                self.advance()

                while self.current_char() not in (None, "\n"):
                    self.advance()
                continue

            if current == "/" and self.peek() == "*":
                start_line = self.line
                start_column = self.column

                self.advance()
                self.advance()

                while True:
                    if self.current_char() is None:
                        raise LexicalError(
                            message="Comentario multilínea no cerrado",
                            line=start_line,
                            column=start_column,
                            character="/",
                        )

                    if self.current_char() == "*" and self.peek() == "/":
                        self.advance()
                        self.advance()
                        break

                    self.advance()

                continue

            break

    def scan_identifier_or_keyword(self) -> Token:
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
        start_line = self.line
        start_column = self.column
        lexeme_chars = []

        while self.current_char() is not None and self.current_char().isdigit():
            lexeme_chars.append(self.current_char())
            self.advance()

        if self.current_char() == ".":
            lexeme_chars.append(".")
            self.advance()

            if self.current_char() is None or not self.current_char().isdigit():
                raise LexicalError(
                    message="Número real mal formado",
                    line=start_line,
                    column=start_column,
                    character="".join(lexeme_chars),
                )

            while self.current_char() is not None and self.current_char().isdigit():
                lexeme_chars.append(self.current_char())
                self.advance()

            if self.current_char() == ".":
                raise LexicalError(
                    message="Número mal formado",
                    line=start_line,
                    column=start_column,
                    character="".join(lexeme_chars) + ".",
                )

            if self.current_char() is not None and (
                self.current_char().isalpha() or self.current_char() == "_"
            ):
                raise LexicalError(
                    message="Número mal formado",
                    line=start_line,
                    column=start_column,
                    character="".join(lexeme_chars) + self.current_char(),
                )

            return Token(TokenType.REAL, "".join(lexeme_chars), start_line, start_column)

        if self.current_char() is not None and (
            self.current_char().isalpha() or self.current_char() == "_"
        ):
            raise LexicalError(
                message="Número entero mal formado",
                line=start_line,
                column=start_column,
                character="".join(lexeme_chars) + self.current_char(),
            )

        return Token(TokenType.INTEGER, "".join(lexeme_chars), start_line, start_column)

    def scan_string(self) -> Token:
        start_line = self.line
        start_column = self.column

        self.advance()
        lexeme_chars = []

        while self.current_char() is not None and self.current_char() != '"':
            if self.current_char() == "\n":
                raise LexicalError(
                    message="Cadena no cerrada",
                    line=start_line,
                    column=start_column,
                    character='"',
                )

            lexeme_chars.append(self.current_char())
            self.advance()

        if self.current_char() != '"':
            raise LexicalError(
                message="Cadena no cerrada",
                line=start_line,
                column=start_column,
                character='"',
            )

        self.advance()
        return Token(TokenType.STRING, "".join(lexeme_chars), start_line, start_column)

    def scan_char(self) -> Token:
        start_line = self.line
        start_column = self.column

        self.advance()
        current = self.current_char()

        if current is None or current == "\n":
            raise LexicalError(
                message="Carácter inválido",
                line=start_line,
                column=start_column,
                character="'",
            )

        if current == "\\":
            self.advance()
            escape_char = self.current_char()

            valid_escapes = {
                "n": "\n",
                "t": "\t",
                "'": "'",
                "\\": "\\",
            }

            if escape_char not in valid_escapes:
                raise LexicalError(
                    message="Secuencia de escape inválida",
                    line=start_line,
                    column=start_column,
                    character="\\" + (escape_char or ""),
                )

            value = valid_escapes[escape_char]
            self.advance()
        else:
            if current == "'":
                raise LexicalError(
                    message="Carácter vacío",
                    line=start_line,
                    column=start_column,
                    character="'",
                )

            value = current
            self.advance()

        if self.current_char() != "'":
            raise LexicalError(
                message="Carácter no cerrado o demasiado largo",
                line=start_line,
                column=start_column,
                character=value,
            )

        self.advance()
        return Token(TokenType.CHAR, value, start_line, start_column)

    def scan_operator_or_delimiter(self) -> Token:
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
            "&&": TokenType.AND,
            "||": TokenType.OR,
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
            "%": TokenType.MODULO,
            "=": TokenType.ASSIGN,
            "<": TokenType.LESS,
            ">": TokenType.GREATER,
            "!": TokenType.NOT,
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