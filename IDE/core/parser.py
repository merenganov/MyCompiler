# IDE/core/parser.py

from typing import List, Optional, Set, Tuple

from core.syntax_error import SyntaxErrorCompiler
from core.syntax_node import SyntaxNode
from core.token_model import Token
from core.token_type import TokenType


class Parser:
    """
    Analizador sintáctico descendente recursivo.

    Recibe la lista de tokens generada por lexer.tokenize()
    y construye un árbol sintáctico usando SyntaxNode.
    """

    TYPE_TOKENS = {
        TokenType.INT,
        TokenType.FLOAT,
        TokenType.REAL_TYPE,
    }

    LITERAL_TOKENS = {
        TokenType.INTEGER,
        TokenType.REAL,
        TokenType.STRING,
        TokenType.CHAR,
    }

    def __init__(self, tokens: List[Token]) -> None:
        self.tokens = tokens if tokens is not None else []
        self.position = 0

    # =========================================================
    # Métodos auxiliares
    # =========================================================

    def current_token(self) -> Optional[Token]:
        if self.position >= len(self.tokens):
            return None
        return self.tokens[self.position]

    def previous_token(self) -> Optional[Token]:
        if self.position - 1 < 0:
            return None
        return self.tokens[self.position - 1]

    def peek_type(self, offset: int = 1) -> Optional[TokenType]:
        index = self.position + offset
        if index >= len(self.tokens):
            return None
        return self.tokens[index].token_type

    def is_at_end(self) -> bool:
        token = self.current_token()
        return token is None or token.token_type == TokenType.EOF

    def check(self, token_type: TokenType) -> bool:
        token = self.current_token()
        if token is None:
            return False
        return token.token_type == token_type

    def check_any(self, token_types: Set[TokenType]) -> bool:
        token = self.current_token()
        if token is None:
            return False
        return token.token_type in token_types

    def advance(self) -> Optional[Token]:
        token = self.current_token()

        if not self.is_at_end():
            self.position += 1

        return token

    def match(self, *token_types: TokenType) -> Optional[Token]:
        for token_type in token_types:
            if self.check(token_type):
                return self.advance()
        return None

    def consume(self, token_type: TokenType, message: str) -> Token:
        token = self.current_token()

        if token is not None and token.token_type == token_type:
            self.position += 1
            return token

        expected = token_type.name
        raise SyntaxErrorCompiler(message, token, expected)

    def consume_any(self, token_types: Set[TokenType], message: str) -> Token:
        token = self.current_token()

        if token is not None and token.token_type in token_types:
            self.position += 1
            return token

        expected = ", ".join(token_type.name for token_type in token_types)
        raise SyntaxErrorCompiler(message, token, expected)

    def token_node(self, name: str, token: Token) -> SyntaxNode:
        return SyntaxNode(name, token)

    def optional_semicolon(self, parent_node: SyntaxNode) -> None:
        semicolon = self.match(TokenType.SEMICOLON)
        if semicolon is not None:
            parent_node.add_child(self.token_node("PUNTO_COMA", semicolon))

    # =========================================================
    # Entrada principal
    # =========================================================

    def parse(self) -> SyntaxNode:
        root = SyntaxNode("PROGRAMA")

        while not self.is_at_end():
            root.add_child(self.statement())

        return root

    # =========================================================
    # Sentencias
    # =========================================================

    def statement(self) -> SyntaxNode:
        token = self.current_token()

        if token is None:
            raise SyntaxErrorCompiler("Fin inesperado del archivo", token)

        if self.check(TokenType.SEMICOLON):
            semicolon = self.advance()
            return self.token_node("SENTENCIA_VACIA", semicolon)

        if self.check(TokenType.MAIN):
            return self.main_statement()

        if self.check_any(self.TYPE_TOKENS):
            return self.declaration()

        if self.check(TokenType.IDENTIFIER):
            return self.identifier_statement()

        if self.check(TokenType.INCREMENT) or self.check(TokenType.DECREMENT):
            return self.prefix_increment_statement()

        if self.check(TokenType.IF):
            return self.if_statement()

        if self.check(TokenType.WHILE):
            return self.while_statement()

        if self.check(TokenType.DO):
            return self.do_statement()

        if self.check(TokenType.COUT):
            return self.cout_statement()

        if self.check(TokenType.CIN):
            return self.cin_statement()

        if self.check(TokenType.LBRACE):
            return self.block()

        raise SyntaxErrorCompiler(
            "Se esperaba una sentencia válida",
            token,
            "declaración, asignación, if, while, do, cin, cout, main o bloque"
        )

    # =========================================================
    # main
    # =========================================================

    def main_statement(self) -> SyntaxNode:
        node = SyntaxNode("FUNCION_MAIN")

        main_token = self.consume(TokenType.MAIN, "Se esperaba 'main'")
        node.add_child(self.token_node("MAIN", main_token))

        if self.match(TokenType.LPAREN) is not None:
            node.add_child(self.token_node("PARENTESIS_IZQUIERDO", self.previous_token()))

            right = self.consume(
                TokenType.RPAREN,
                "Se esperaba ')' después de '(' en main"
            )
            node.add_child(self.token_node("PARENTESIS_DERECHO", right))

        if not self.check(TokenType.LBRACE):
            raise SyntaxErrorCompiler(
                "Se esperaba un bloque '{ ... }' después de main",
                self.current_token(),
                "LBRACE"
            )

        node.add_child(self.block())
        return node

    # =========================================================
    # Bloques
    # =========================================================

    def block(self) -> SyntaxNode:
        node = SyntaxNode("BLOQUE")

        left = self.consume(TokenType.LBRACE, "Se esperaba '{' para iniciar el bloque")
        node.add_child(self.token_node("LLAVE_IZQUIERDA", left))

        while not self.is_at_end() and not self.check(TokenType.RBRACE):
            node.add_child(self.statement())

        right = self.consume(TokenType.RBRACE, "Se esperaba '}' para cerrar el bloque")
        node.add_child(self.token_node("LLAVE_DERECHA", right))

        return node

    def parse_until(self, stop_tokens: Set[TokenType], node_name: str) -> SyntaxNode:
        node = SyntaxNode(node_name)

        while not self.is_at_end() and not self.check_any(stop_tokens):
            node.add_child(self.statement())

        return node

    # =========================================================
    # Declaraciones
    # Ejemplos:
    # int x;
    # int x = 10;
    # float a, b = 2.5;
    # real promedio = 9.8;
    # =========================================================

    def declaration(self) -> SyntaxNode:
        node = SyntaxNode("DECLARACION")

        type_token = self.consume_any(
            self.TYPE_TOKENS,
            "Se esperaba un tipo de dato"
        )
        node.add_child(self.token_node("TIPO_DATO", type_token))

        variables_node = SyntaxNode("VARIABLES")

        while True:
            variable_node = SyntaxNode("VARIABLE")

            identifier = self.consume(
                TokenType.IDENTIFIER,
                "Se esperaba un identificador después del tipo de dato"
            )
            variable_node.add_child(self.token_node("IDENTIFICADOR", identifier))

            assign = self.match(TokenType.ASSIGN)
            if assign is not None:
                variable_node.add_child(self.token_node("ASIGNACION", assign))
                variable_node.add_child(self.expression())

            variables_node.add_child(variable_node)

            comma = self.match(TokenType.COMMA)
            if comma is None:
                break

            variables_node.add_child(self.token_node("COMA", comma))

        node.add_child(variables_node)

        semicolon = self.consume(
            TokenType.SEMICOLON,
            "Se esperaba ';' al final de la declaración"
        )
        node.add_child(self.token_node("PUNTO_COMA", semicolon))

        return node

    # =========================================================
    # Sentencias que empiezan con identificador
    # Ejemplos:
    # x = 10;
    # x++;
    # x--;
    # funcion(a, b);
    # =========================================================

    def identifier_statement(self) -> SyntaxNode:
        identifier = self.consume(TokenType.IDENTIFIER, "Se esperaba un identificador")

        if self.check(TokenType.LPAREN):
            node = SyntaxNode("SENTENCIA_LLAMADA_FUNCION")
            node.add_child(self.finish_function_call(identifier))

            semicolon = self.consume(
                TokenType.SEMICOLON,
                "Se esperaba ';' al final de la llamada a función"
            )
            node.add_child(self.token_node("PUNTO_COMA", semicolon))
            return node

        assign = self.match(TokenType.ASSIGN)
        if assign is not None:
            node = SyntaxNode("ASIGNACION")
            node.add_child(self.token_node("IDENTIFICADOR", identifier))
            node.add_child(self.token_node("OPERADOR_ASIGNACION", assign))
            node.add_child(self.expression())

            semicolon = self.consume(
                TokenType.SEMICOLON,
                "Se esperaba ';' al final de la asignación"
            )
            node.add_child(self.token_node("PUNTO_COMA", semicolon))

            return node

        increment = self.match(TokenType.INCREMENT, TokenType.DECREMENT)
        if increment is not None:
            node = SyntaxNode("INCREMENTO_DECREMENTO")
            node.add_child(self.token_node("IDENTIFICADOR", identifier))
            node.add_child(self.token_node("OPERADOR", increment))

            semicolon = self.consume(
                TokenType.SEMICOLON,
                "Se esperaba ';' después del incremento o decremento"
            )
            node.add_child(self.token_node("PUNTO_COMA", semicolon))

            return node

        raise SyntaxErrorCompiler(
            "Después de un identificador se esperaba '=', '++', '--' o '('",
            self.current_token(),
            "ASSIGN, INCREMENT, DECREMENT o LPAREN"
        )

    def prefix_increment_statement(self) -> SyntaxNode:
        node = SyntaxNode("INCREMENTO_DECREMENTO_PREFIJO")

        operator = self.consume_any(
            {TokenType.INCREMENT, TokenType.DECREMENT},
            "Se esperaba '++' o '--'"
        )
        node.add_child(self.token_node("OPERADOR", operator))

        identifier = self.consume(
            TokenType.IDENTIFIER,
            "Se esperaba un identificador después de '++' o '--'"
        )
        node.add_child(self.token_node("IDENTIFICADOR", identifier))

        semicolon = self.consume(
            TokenType.SEMICOLON,
            "Se esperaba ';' después del incremento o decremento"
        )
        node.add_child(self.token_node("PUNTO_COMA", semicolon))

        return node

    # =========================================================
    # if
    # Soporta:
    # if (x > 0) { ... }
    # if (x > 0) { ... } else { ... }
    # if x > 0 then ... else ... end
    # =========================================================

    def if_statement(self) -> SyntaxNode:
        node = SyntaxNode("CONDICIONAL_IF")

        if_token = self.consume(TokenType.IF, "Se esperaba 'if'")
        node.add_child(self.token_node("IF", if_token))

        node.add_child(self.condition())

        then_token = self.match(TokenType.THEN)

        if then_token is not None:
            node.add_child(self.token_node("THEN", then_token))

            then_block = self.parse_until(
                {TokenType.ELSE, TokenType.END},
                "BLOQUE_THEN"
            )
            node.add_child(then_block)

            else_token = self.match(TokenType.ELSE)
            if else_token is not None:
                else_node = SyntaxNode("BLOQUE_ELSE")
                else_node.add_child(self.token_node("ELSE", else_token))
                else_node.add_child(
                    self.parse_until({TokenType.END}, "SENTENCIAS_ELSE")
                )
                node.add_child(else_node)

            end_token = self.consume(
                TokenType.END,
                "Se esperaba 'end' para cerrar el if"
            )
            node.add_child(self.token_node("END", end_token))

            self.optional_semicolon(node)
            return node

        then_block = SyntaxNode("BLOQUE_THEN")

        if self.check(TokenType.LBRACE):
            then_block.add_child(self.block())
        else:
            then_block.add_child(self.statement())

        node.add_child(then_block)

        else_token = self.match(TokenType.ELSE)
        if else_token is not None:
            else_node = SyntaxNode("BLOQUE_ELSE")
            else_node.add_child(self.token_node("ELSE", else_token))

            if self.check(TokenType.IF):
                else_node.add_child(self.if_statement())
            elif self.check(TokenType.LBRACE):
                else_node.add_child(self.block())
            else:
                else_node.add_child(self.statement())

            node.add_child(else_node)

        return node

    # =========================================================
    # while
    # Soporta:
    # while (x < 10) { ... }
    # while x < 10 do ... end
    # =========================================================

    def while_statement(self) -> SyntaxNode:
        node = SyntaxNode("CICLO_WHILE")

        while_token = self.consume(TokenType.WHILE, "Se esperaba 'while'")
        node.add_child(self.token_node("WHILE", while_token))

        node.add_child(self.condition())

        do_token = self.match(TokenType.DO)

        if do_token is not None:
            node.add_child(self.token_node("DO", do_token))

            body = self.parse_until({TokenType.END}, "CUERPO_WHILE")
            node.add_child(body)

            end_token = self.consume(
                TokenType.END,
                "Se esperaba 'end' para cerrar el while"
            )
            node.add_child(self.token_node("END", end_token))

            self.optional_semicolon(node)
            return node

        if self.check(TokenType.LBRACE):
            node.add_child(self.block())
        else:
            node.add_child(self.statement())

        return node

    # =========================================================
    # do-until / do-while
    # Soporta:
    # do { ... } while (x < 10);
    # do ... until x == 10;
    # =========================================================

    def do_statement(self) -> SyntaxNode:
        node = SyntaxNode("CICLO_DO")

        do_token = self.consume(TokenType.DO, "Se esperaba 'do'")
        node.add_child(self.token_node("DO", do_token))

        if self.check(TokenType.LBRACE):
            node.add_child(self.block())
        else:
            node.add_child(
                self.parse_until(
                    {TokenType.WHILE, TokenType.UNTIL},
                    "CUERPO_DO"
                )
            )

        if self.check(TokenType.WHILE):
            while_token = self.consume(TokenType.WHILE, "Se esperaba 'while'")
            node.add_child(self.token_node("WHILE", while_token))
            node.add_child(self.condition())
            self.optional_semicolon(node)
            return node

        if self.check(TokenType.UNTIL):
            until_token = self.consume(TokenType.UNTIL, "Se esperaba 'until'")
            node.add_child(self.token_node("UNTIL", until_token))
            node.add_child(self.condition())
            self.optional_semicolon(node)
            return node

        raise SyntaxErrorCompiler(
            "Se esperaba 'while' o 'until' después del cuerpo del do",
            self.current_token(),
            "WHILE o UNTIL"
        )

    # =========================================================
    # cin / cout
    # Soporta:
    # cout(x);
    # cout << x;
    # cin(x);
    # cin >> x;
    #
    # Nota: tu lexer no tiene TokenType para << o >>.
    # Por eso aquí se interpretan como LESS LESS y GREATER GREATER.
    # =========================================================

    def cout_statement(self) -> SyntaxNode:
        node = SyntaxNode("SALIDA_COUT")

        cout_token = self.consume(TokenType.COUT, "Se esperaba 'cout'")
        node.add_child(self.token_node("COUT", cout_token))

        left_paren = self.match(TokenType.LPAREN)
        if left_paren is not None:
            node.add_child(self.token_node("PARENTESIS_IZQUIERDO", left_paren))
            node.add_child(self.expression())

            right_paren = self.consume(
                TokenType.RPAREN,
                "Se esperaba ')' después de la expresión en cout"
            )
            node.add_child(self.token_node("PARENTESIS_DERECHO", right_paren))

            semicolon = self.consume(
                TokenType.SEMICOLON,
                "Se esperaba ';' al final de cout"
            )
            node.add_child(self.token_node("PUNTO_COMA", semicolon))
            return node

        output_operator = self.match_double(TokenType.LESS)
        if output_operator is not None:
            node.add_child(self.double_operator_node("OPERADOR_SALIDA", output_operator))

            values_node = SyntaxNode("VALORES_SALIDA")
            values_node.add_child(self.expression())

            while True:
                next_operator = self.match_double(TokenType.LESS)
                if next_operator is None:
                    break

                values_node.add_child(
                    self.double_operator_node("OPERADOR_SALIDA", next_operator)
                )
                values_node.add_child(self.expression())

            node.add_child(values_node)

            semicolon = self.consume(
                TokenType.SEMICOLON,
                "Se esperaba ';' al final de cout"
            )
            node.add_child(self.token_node("PUNTO_COMA", semicolon))
            return node

        raise SyntaxErrorCompiler(
            "Después de cout se esperaba '(' o '<<'",
            self.current_token(),
            "LPAREN o LESS LESS"
        )

    def cin_statement(self) -> SyntaxNode:
        node = SyntaxNode("ENTRADA_CIN")

        cin_token = self.consume(TokenType.CIN, "Se esperaba 'cin'")
        node.add_child(self.token_node("CIN", cin_token))

        left_paren = self.match(TokenType.LPAREN)
        if left_paren is not None:
            node.add_child(self.token_node("PARENTESIS_IZQUIERDO", left_paren))

            identifiers_node = SyntaxNode("IDENTIFICADORES_ENTRADA")

            identifier = self.consume(
                TokenType.IDENTIFIER,
                "Se esperaba un identificador en cin"
            )
            identifiers_node.add_child(self.token_node("IDENTIFICADOR", identifier))

            while True:
                comma = self.match(TokenType.COMMA)
                if comma is None:
                    break

                identifiers_node.add_child(self.token_node("COMA", comma))

                identifier = self.consume(
                    TokenType.IDENTIFIER,
                    "Se esperaba un identificador después de ',' en cin"
                )
                identifiers_node.add_child(self.token_node("IDENTIFICADOR", identifier))

            node.add_child(identifiers_node)

            right_paren = self.consume(
                TokenType.RPAREN,
                "Se esperaba ')' después de los identificadores en cin"
            )
            node.add_child(self.token_node("PARENTESIS_DERECHO", right_paren))

            semicolon = self.consume(
                TokenType.SEMICOLON,
                "Se esperaba ';' al final de cin"
            )
            node.add_child(self.token_node("PUNTO_COMA", semicolon))
            return node

        input_operator = self.match_double(TokenType.GREATER)
        if input_operator is not None:
            node.add_child(self.double_operator_node("OPERADOR_ENTRADA", input_operator))

            identifiers_node = SyntaxNode("IDENTIFICADORES_ENTRADA")

            identifier = self.consume(
                TokenType.IDENTIFIER,
                "Se esperaba un identificador después de '>>'"
            )
            identifiers_node.add_child(self.token_node("IDENTIFICADOR", identifier))

            while True:
                next_operator = self.match_double(TokenType.GREATER)
                if next_operator is None:
                    break

                identifiers_node.add_child(
                    self.double_operator_node("OPERADOR_ENTRADA", next_operator)
                )

                identifier = self.consume(
                    TokenType.IDENTIFIER,
                    "Se esperaba un identificador después de '>>'"
                )
                identifiers_node.add_child(self.token_node("IDENTIFICADOR", identifier))

            node.add_child(identifiers_node)

            semicolon = self.consume(
                TokenType.SEMICOLON,
                "Se esperaba ';' al final de cin"
            )
            node.add_child(self.token_node("PUNTO_COMA", semicolon))
            return node

        raise SyntaxErrorCompiler(
            "Después de cin se esperaba '(' o '>>'",
            self.current_token(),
            "LPAREN o GREATER GREATER"
        )

    def match_double(self, token_type: TokenType) -> Optional[Tuple[Token, Token]]:
        if self.check(token_type) and self.peek_type(1) == token_type:
            first = self.advance()
            second = self.advance()
            return first, second

        return None

    def double_operator_node(self, name: str, tokens: Tuple[Token, Token]) -> SyntaxNode:
        node = SyntaxNode(name)
        node.add_child(self.token_node(tokens[0].token_type.name, tokens[0]))
        node.add_child(self.token_node(tokens[1].token_type.name, tokens[1]))
        return node

    # =========================================================
    # Condiciones
    # =========================================================

    def condition(self) -> SyntaxNode:
        node = SyntaxNode("CONDICION")

        left_paren = self.match(TokenType.LPAREN)
        if left_paren is not None:
            node.add_child(self.token_node("PARENTESIS_IZQUIERDO", left_paren))
            node.add_child(self.expression())

            right_paren = self.consume(
                TokenType.RPAREN,
                "Se esperaba ')' después de la condición"
            )
            node.add_child(self.token_node("PARENTESIS_DERECHO", right_paren))
            return node

        node.add_child(self.expression())
        return node

    # =========================================================
    # Llamadas a función
    # =========================================================

    def finish_function_call(self, identifier_token: Token) -> SyntaxNode:
        node = SyntaxNode("LLAMADA_FUNCION")
        node.add_child(self.token_node("IDENTIFICADOR", identifier_token))

        left = self.consume(
            TokenType.LPAREN,
            "Se esperaba '(' en la llamada a función"
        )
        node.add_child(self.token_node("PARENTESIS_IZQUIERDO", left))

        arguments_node = SyntaxNode("ARGUMENTOS")

        if not self.check(TokenType.RPAREN):
            arguments_node.add_child(self.expression())

            while True:
                comma = self.match(TokenType.COMMA)
                if comma is None:
                    break

                arguments_node.add_child(self.token_node("COMA", comma))
                arguments_node.add_child(self.expression())

        node.add_child(arguments_node)

        right = self.consume(
            TokenType.RPAREN,
            "Se esperaba ')' para cerrar la llamada a función"
        )
        node.add_child(self.token_node("PARENTESIS_DERECHO", right))

        return node

    # =========================================================
    # Expresiones con precedencia
    # =========================================================

    def expression(self) -> SyntaxNode:
        node = SyntaxNode("EXPRESION")
        node.add_child(self.logical_or())
        return node

    def logical_or(self) -> SyntaxNode:
        node = self.logical_and()

        while True:
            operator = self.match(TokenType.OR)
            if operator is None:
                break

            node = self.binary_node("OPERACION_OR", node, operator, self.logical_and())

        return node

    def logical_and(self) -> SyntaxNode:
        node = self.equality()

        while True:
            operator = self.match(TokenType.AND)
            if operator is None:
                break

            node = self.binary_node("OPERACION_AND", node, operator, self.equality())

        return node

    def equality(self) -> SyntaxNode:
        node = self.comparison()

        while True:
            operator = self.match(TokenType.EQUAL, TokenType.NOT_EQUAL)
            if operator is None:
                break

            node = self.binary_node("OPERACION_IGUALDAD", node, operator, self.comparison())

        return node

    def comparison(self) -> SyntaxNode:
        node = self.term()

        while True:
            # Evita que cout << x y cin >> x se interpreten como comparaciones.
            if self.check(TokenType.LESS) and self.peek_type(1) == TokenType.LESS:
                break

            if self.check(TokenType.GREATER) and self.peek_type(1) == TokenType.GREATER:
                break

            operator = self.match(
                TokenType.LESS,
                TokenType.LESS_EQUAL,
                TokenType.GREATER,
                TokenType.GREATER_EQUAL,
            )

            if operator is None:
                break

            node = self.binary_node("OPERACION_COMPARACION", node, operator, self.term())

        return node

    def term(self) -> SyntaxNode:
        node = self.factor()

        while True:
            operator = self.match(TokenType.PLUS, TokenType.MINUS)
            if operator is None:
                break

            node = self.binary_node("OPERACION_SUMA_RESTA", node, operator, self.factor())

        return node

    def factor(self) -> SyntaxNode:
        node = self.power()

        while True:
            operator = self.match(TokenType.STAR, TokenType.SLASH, TokenType.MODULO)
            if operator is None:
                break

            node = self.binary_node(
                "OPERACION_MULTIPLICACION_DIVISION",
                node,
                operator,
                self.power()
            )

        return node

    def power(self) -> SyntaxNode:
        node = self.unary()

        while True:
            operator = self.match(TokenType.POWER)
            if operator is None:
                break

            node = self.binary_node("OPERACION_POTENCIA", node, operator, self.unary())

        return node

    def unary(self) -> SyntaxNode:
        operator = self.match(
            TokenType.NOT,
            TokenType.MINUS,
            TokenType.PLUS,
            TokenType.INCREMENT,
            TokenType.DECREMENT,
        )

        if operator is not None:
            node = SyntaxNode("OPERACION_UNARIA")
            node.add_child(self.token_node("OPERADOR", operator))
            node.add_child(self.unary())
            return node

        return self.primary()

    def primary(self) -> SyntaxNode:
        token = self.current_token()

        if token is None:
            raise SyntaxErrorCompiler("Se esperaba una expresión", token)

        literal = self.match(
            TokenType.INTEGER,
            TokenType.REAL,
            TokenType.STRING,
            TokenType.CHAR,
        )

        if literal is not None:
            if literal.token_type in {TokenType.INTEGER, TokenType.REAL}:
                return self.token_node("NUMERO", literal)

            if literal.token_type == TokenType.STRING:
                return self.token_node("CADENA", literal)

            if literal.token_type == TokenType.CHAR:
                return self.token_node("CARACTER", literal)

        identifier = self.match(TokenType.IDENTIFIER)
        if identifier is not None:
            if self.check(TokenType.LPAREN):
                return self.finish_function_call(identifier)

            return self.token_node("IDENTIFICADOR", identifier)

        left_paren = self.match(TokenType.LPAREN)
        if left_paren is not None:
            node = SyntaxNode("EXPRESION_AGRUPADA")
            node.add_child(self.token_node("PARENTESIS_IZQUIERDO", left_paren))
            node.add_child(self.expression())

            right_paren = self.consume(
                TokenType.RPAREN,
                "Se esperaba ')' después de la expresión"
            )
            node.add_child(self.token_node("PARENTESIS_DERECHO", right_paren))

            return node

        raise SyntaxErrorCompiler(
            "Se esperaba un identificador, número, cadena, carácter o expresión entre paréntesis",
            token,
            "IDENTIFIER, INTEGER, REAL, STRING, CHAR o LPAREN"
        )

    def binary_node(
        self,
        name: str,
        left: SyntaxNode,
        operator: Token,
        right: SyntaxNode
    ) -> SyntaxNode:
        node = SyntaxNode(name)
        node.add_child(left)
        node.add_child(self.token_node("OPERADOR", operator))
        node.add_child(right)
        return node