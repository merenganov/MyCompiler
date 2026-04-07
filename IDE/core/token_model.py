from dataclasses import dataclass

from core.token_type import TokenType


@dataclass(frozen=True)
class Token:
    # Representa una unidad léxica producida por el analizador.
    token_type: TokenType
    lexeme: str
    line: int
    column: int

    def __str__(self) -> str:
        return (
            f"Token(type={self.token_type.name}, "
            f"lexeme={self.lexeme!r}, "
            f"line={self.line}, "
            f"column={self.column})"
        )