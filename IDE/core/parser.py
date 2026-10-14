# IDE/core/parser.py



from typing import List, Optional, Set, Tuple



from core.syntax_error import SyntaxErrorCompiler

from core.syntax_node import SyntaxNode

from core.token_model import Token

from core.token_type import TokenType





class Parser:

    """

    Analizador sintáctico descendente recursivo.



    Esta versión genera un árbol sintáctico más abstracto, parecido a un AST:



    Ejemplo:

        y = y + 1;



    Árbol:

        =

        ├── y <ID>

        └── +

            ├── y <ID>

            └── 1 <INT>



    El parser sigue validando:

    - ;

    - ()

    - {}

    - then

    - end

    - else



    Pero esos símbolos ya no se agregan al árbol porque no son relevantes

    para la estructura abstracta.

    """



    TYPE_TOKENS = {

        TokenType.INT,

        TokenType.FLOAT,

        TokenType.REAL_TYPE,

    }



    def __init__(self, tokens: List[Token]) -> None:

        self.tokens = tokens if tokens is not None else []

        self.position = 0



    # =========================================================

    # MÉTODOS AUXILIARES

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

        return token is not None and token.token_type == token_type



    def check_any(self, token_types: Set[TokenType]) -> bool:

        token = self.current_token()

        return token is not None and token.token_type in token_types



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



        raise SyntaxErrorCompiler(message, token, token_type.name)



    def consume_any(self, token_types: Set[TokenType], message: str) -> Token:

        token = self.current_token()



        if token is not None and token.token_type in token_types:

            self.position += 1

            return token



        expected = ", ".join(token_type.name for token_type in token_types)

        raise SyntaxErrorCompiler(message, token, expected)



    def token_node(self, name: str, token: Token) -> SyntaxNode:

        return SyntaxNode(name, token)



    def optional_semicolon(self) -> None:

        self.match(TokenType.SEMICOLON)



    # =========================================================

    # ENTRADA PRINCIPAL

    # =========================================================



    def parse(self) -> SyntaxNode:

        root = SyntaxNode("PROGRAMA")



        while not self.is_at_end():

            root.add_child(self.statement())



        return root



    # =========================================================

    # SENTENCIAS

    # =========================================================



    def statement(self) -> Optional[SyntaxNode]:

        token = self.current_token()



        if token is None:

            raise SyntaxErrorCompiler("Fin inesperado del archivo", token)



        if self.check(TokenType.SEMICOLON):

            self.advance()

            return None



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

    # MAIN

    # =========================================================



    def main_statement(self) -> SyntaxNode:

        node = SyntaxNode("MAIN")



        self.consume(TokenType.MAIN, "Se esperaba 'main'")



        if self.match(TokenType.LPAREN) is not None:

            self.consume(

                TokenType.RPAREN,

                "Se esperaba ')' después de '(' en main"

            )



        if not self.check(TokenType.LBRACE):

            raise SyntaxErrorCompiler(

                "Se esperaba un bloque '{ ... }' después de main",

                self.current_token(),

                "LBRACE"

            )



        node.add_child(self.block())

        return node



    # =========================================================

    # BLOQUES

    # =========================================================



    def block(self) -> SyntaxNode:

        node = SyntaxNode("BLOQUE")



        self.consume(TokenType.LBRACE, "Se esperaba '{' para iniciar el bloque")



        while not self.is_at_end() and not self.check(TokenType.RBRACE):

            node.add_child(self.statement())



        self.consume(TokenType.RBRACE, "Se esperaba '}' para cerrar el bloque")



        return node



    def parse_until(self, stop_tokens: Set[TokenType], node_name: str) -> SyntaxNode:

        node = SyntaxNode(node_name)



        while not self.is_at_end() and not self.check_any(stop_tokens):

            node.add_child(self.statement())



        return node



    # =========================================================

    # DECLARACIONES

    # Ejemplos:

    # int x,y,z;

    # real a,b,c;

    # int x = 5;

    # =========================================================



    def declaration(self) -> SyntaxNode:

        type_token = self.consume_any(

            self.TYPE_TOKENS,

            "Se esperaba un tipo de dato"

        )



        node = SyntaxNode("DECLARAR", type_token)



        while True:

            identifier = self.consume(

                TokenType.IDENTIFIER,

                "Se esperaba un identificador después del tipo de dato"

            )



            assign = self.match(TokenType.ASSIGN)



            if assign is not None:

                assign_node = SyntaxNode("OPERADOR", assign)

                assign_node.add_child(self.token_node("IDENTIFICADOR", identifier))

                assign_node.add_child(self.expression())

                node.add_child(assign_node)

            else:

                node.add_child(self.token_node("IDENTIFICADOR", identifier))



            comma = self.match(TokenType.COMMA)

            if comma is None:

                break



        self.consume(

            TokenType.SEMICOLON,

            "Se esperaba ';' al final de la declaración"

        )



        return node



    # =========================================================

    # ASIGNACIONES, INCREMENTOS Y LLAMADAS

    # Ejemplos:

    # x = 10;

    # x++;

    # x--;

    # funcion(a, b);

    # =========================================================



    def identifier_statement(self) -> SyntaxNode:

        identifier = self.consume(TokenType.IDENTIFIER, "Se esperaba un identificador")



        if self.check(TokenType.LPAREN):

            node = self.finish_function_call(identifier)



            self.consume(

                TokenType.SEMICOLON,

                "Se esperaba ';' al final de la llamada a función"

            )



            return node



        assign = self.match(TokenType.ASSIGN)

        if assign is not None:

            node = SyntaxNode("OPERADOR", assign)

            node.add_child(self.token_node("IDENTIFICADOR", identifier))

            node.add_child(self.expression())



            self.consume(

                TokenType.SEMICOLON,

                "Se esperaba ';' al final de la asignación"

            )



            return node



        increment = self.match(TokenType.INCREMENT, TokenType.DECREMENT)

        if increment is not None:

            node = SyntaxNode("OPERADOR", increment)

            node.add_child(self.token_node("IDENTIFICADOR", identifier))



            self.consume(

                TokenType.SEMICOLON,

                "Se esperaba ';' después del incremento o decremento"

            )



            return node



        raise SyntaxErrorCompiler(

            "Después de un identificador se esperaba '=', '++', '--' o '('",

            self.current_token(),

            "ASSIGN, INCREMENT, DECREMENT o LPAREN"

        )



    def prefix_increment_statement(self) -> SyntaxNode:

        operator = self.consume_any(

            {TokenType.INCREMENT, TokenType.DECREMENT},

            "Se esperaba '++' o '--'"

        )



        identifier = self.consume(

            TokenType.IDENTIFIER,

            "Se esperaba un identificador después de '++' o '--'"

        )



        node = SyntaxNode("OPERADOR", operator)

        node.add_child(self.token_node("IDENTIFICADOR", identifier))



        self.consume(

            TokenType.SEMICOLON,

            "Se esperaba ';' después del incremento o decremento"

        )



        return node



    # =========================================================

    # IF

    # Soporta:

    # if (condicion) then ... else ... end;

    # if (condicion) { ... } else { ... }

    # =========================================================



    def if_statement(self) -> SyntaxNode:

        node = SyntaxNode("IF")



        self.consume(TokenType.IF, "Se esperaba 'if'")

        node.add_child(self.condition())



        then_token = self.match(TokenType.THEN)



        if then_token is not None:

            then_node = self.parse_until(

                {TokenType.ELSE, TokenType.END},

                "THEN"

            )

            node.add_child(then_node)



            else_token = self.match(TokenType.ELSE)

            if else_token is not None:

                else_node = self.parse_until({TokenType.END}, "ELSE")

                node.add_child(else_node)



            self.consume(

                TokenType.END,

                "Se esperaba 'end' para cerrar el if"

            )



            self.optional_semicolon()

            return node



        then_node = SyntaxNode("THEN")



        if self.check(TokenType.LBRACE):

            then_node.add_child(self.block())

        else:

            then_node.add_child(self.statement())



        node.add_child(then_node)



        else_token = self.match(TokenType.ELSE)

        if else_token is not None:

            else_node = SyntaxNode("ELSE")



            if self.check(TokenType.IF):

                else_node.add_child(self.if_statement())

            elif self.check(TokenType.LBRACE):

                else_node.add_child(self.block())

            else:

                else_node.add_child(self.statement())



            node.add_child(else_node)



        return node



    # =========================================================

    # WHILE

    # Soporta:

    # while (condicion) { ... }

    # while condicion do ... end;

    # =========================================================



    def while_statement(self) -> SyntaxNode:
        """
        Soporta:

        - while (condicion) { ... }
        - while condicion do ... end;
        - while condicion ... end;

        La última forma es la utilizada por el archivo oficial de prueba.
        """

        node = SyntaxNode("WHILE")

        self.consume(TokenType.WHILE, "Se esperaba 'while'")
        node.add_child(self.condition())

        do_token = self.match(TokenType.DO)

        if do_token is not None:
            body = self.parse_until({TokenType.END}, "CUERPO")
            node.add_child(body)

            self.consume(
                TokenType.END,
                "Se esperaba 'end' para cerrar el while"
            )

            self.optional_semicolon()
            return node

        if self.check(TokenType.LBRACE):
            node.add_child(self.block())
            return node

        body = self.parse_until({TokenType.END}, "CUERPO")
        node.add_child(body)

        self.consume(
            TokenType.END,
            "Se esperaba 'end' para cerrar el while"
        )

        self.optional_semicolon()
        return node


    # =========================================================

    # DO / DO-WHILE / DO-UNTIL

    # Soporta:

    # do { ... } while(condicion);

    # do { ... } until(condicion);

    # =========================================================



    def do_statement(self) -> SyntaxNode:
        """
        Soporta:

        - do { ... } while(condicion);
        - do { ... } until(condicion);
        - do ... until condicion;

        En la forma sin llaves, los while encontrados dentro del cuerpo
        se interpretan como sentencias while anidadas y no como cierre
        del do.
        """

        node = SyntaxNode("DO")

        self.consume(TokenType.DO, "Se esperaba 'do'")

        body_node = SyntaxNode("CUERPO")

        if self.check(TokenType.LBRACE):
            body_node.add_child(self.block())
            node.add_child(body_node)

            if self.check(TokenType.WHILE):
                self.consume(TokenType.WHILE, "Se esperaba 'while'")
                node.name = "DO_WHILE"
                node.add_child(self.condition())
                self.optional_semicolon()
                return node

            if self.check(TokenType.UNTIL):
                self.consume(TokenType.UNTIL, "Se esperaba 'until'")
                node.name = "DO_UNTIL"
                node.add_child(self.condition())
                self.optional_semicolon()
                return node

            raise SyntaxErrorCompiler(
                "Se esperaba 'while' o 'until' después del cuerpo del do",
                self.current_token(),
                "WHILE o UNTIL"
            )

        body = self.parse_until(
            {TokenType.UNTIL},
            "BLOQUE"
        )

        body_node.add_child(body)
        node.add_child(body_node)

        self.consume(
            TokenType.UNTIL,
            "Se esperaba 'until' después del cuerpo del do"
        )

        node.name = "DO_UNTIL"
        node.add_child(self.condition())
        self.optional_semicolon()

        return node


    # =========================================================

    # COUT

    # Soporta:

    # cout(x);

    # cout << x;

    # =========================================================



    def cout_statement(self) -> SyntaxNode:

        node = SyntaxNode("COUT")



        self.consume(TokenType.COUT, "Se esperaba 'cout'")



        left_paren = self.match(TokenType.LPAREN)

        if left_paren is not None:

            node.add_child(self.expression())



            self.consume(

                TokenType.RPAREN,

                "Se esperaba ')' después de la expresión en cout"

            )



            self.consume(

                TokenType.SEMICOLON,

                "Se esperaba ';' al final de cout"

            )



            return node



        output_operator = self.match_double(TokenType.LESS)

        if output_operator is not None:

            node.add_child(self.expression())



            while True:

                next_operator = self.match_double(TokenType.LESS)

                if next_operator is None:

                    break



                node.add_child(self.expression())



            self.consume(

                TokenType.SEMICOLON,

                "Se esperaba ';' al final de cout"

            )



            return node



        raise SyntaxErrorCompiler(

            "Después de cout se esperaba '(' o '<<'",

            self.current_token(),

            "LPAREN o LESS LESS"

        )



    # =========================================================

    # CIN

    # Soporta:

    # cin(x);

    # cin >> x;

    # =========================================================



    def cin_statement(self) -> SyntaxNode:

        node = SyntaxNode("CIN")



        self.consume(TokenType.CIN, "Se esperaba 'cin'")



        left_paren = self.match(TokenType.LPAREN)

        if left_paren is not None:

            identifier = self.consume(

                TokenType.IDENTIFIER,

                "Se esperaba un identificador en cin"

            )

            node.add_child(self.token_node("IDENTIFICADOR", identifier))



            while True:

                comma = self.match(TokenType.COMMA)

                if comma is None:

                    break



                identifier = self.consume(

                    TokenType.IDENTIFIER,

                    "Se esperaba un identificador después de ',' en cin"

                )

                node.add_child(self.token_node("IDENTIFICADOR", identifier))



            self.consume(

                TokenType.RPAREN,

                "Se esperaba ')' después de los identificadores en cin"

            )



            self.consume(

                TokenType.SEMICOLON,

                "Se esperaba ';' al final de cin"

            )



            return node



        input_operator = self.match_double(TokenType.GREATER)

        if input_operator is not None:

            identifier = self.consume(

                TokenType.IDENTIFIER,

                "Se esperaba un identificador después de '>>'"

            )

            node.add_child(self.token_node("IDENTIFICADOR", identifier))



            while True:

                next_operator = self.match_double(TokenType.GREATER)

                if next_operator is None:

                    break



                identifier = self.consume(

                    TokenType.IDENTIFIER,

                    "Se esperaba un identificador después de '>>'"

                )

                node.add_child(self.token_node("IDENTIFICADOR", identifier))



            self.consume(

                TokenType.SEMICOLON,

                "Se esperaba ';' al final de cin"

            )



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



    # =========================================================

    # CONDICIONES

    # =========================================================



    def condition(self) -> SyntaxNode:

        node = SyntaxNode("CONDICION")



        left_paren = self.match(TokenType.LPAREN)

        if left_paren is not None:

            node.add_child(self.expression())



            self.consume(

                TokenType.RPAREN,

                "Se esperaba ')' después de la condición"

            )



            return node



        node.add_child(self.expression())

        return node



    # =========================================================

    # LLAMADAS A FUNCIÓN

    # =========================================================



    def finish_function_call(self, identifier_token: Token) -> SyntaxNode:

        node = SyntaxNode("LLAMAR")

        node.add_child(self.token_node("IDENTIFICADOR", identifier_token))



        self.consume(

            TokenType.LPAREN,

            "Se esperaba '(' en la llamada a función"

        )



        if not self.check(TokenType.RPAREN):

            node.add_child(self.expression())



            while True:

                comma = self.match(TokenType.COMMA)

                if comma is None:

                    break



                node.add_child(self.expression())



        self.consume(

            TokenType.RPAREN,

            "Se esperaba ')' para cerrar la llamada a función"

        )



        return node



    # =========================================================

    # EXPRESIONES CON PRECEDENCIA

    # =========================================================



    def expression(self) -> SyntaxNode:

        return self.logical_or()



    def logical_or(self) -> SyntaxNode:

        node = self.logical_and()



        while True:

            operator = self.match(TokenType.OR)

            if operator is None:

                break



            node = self.binary_node(node, operator, self.logical_and())



        return node



    def logical_and(self) -> SyntaxNode:

        node = self.equality()



        while True:

            operator = self.match(TokenType.AND)

            if operator is None:

                break



            node = self.binary_node(node, operator, self.equality())



        return node



    def equality(self) -> SyntaxNode:

        node = self.comparison()



        while True:

            operator = self.match(TokenType.EQUAL, TokenType.NOT_EQUAL)

            if operator is None:

                break



            node = self.binary_node(node, operator, self.comparison())



        return node



    def comparison(self) -> SyntaxNode:

        node = self.term()



        while True:

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



            node = self.binary_node(node, operator, self.term())



        return node



    def term(self) -> SyntaxNode:

        node = self.factor()



        while True:

            operator = self.match(TokenType.PLUS, TokenType.MINUS)

            if operator is None:

                break



            node = self.binary_node(node, operator, self.factor())



        return node



    def factor(self) -> SyntaxNode:

        node = self.power()



        while True:

            operator = self.match(TokenType.STAR, TokenType.SLASH, TokenType.MODULO)

            if operator is None:

                break



            node = self.binary_node(node, operator, self.power())



        return node



    def power(self) -> SyntaxNode:

        node = self.unary()



        while True:

            operator = self.match(TokenType.POWER)

            if operator is None:

                break



            node = self.binary_node(node, operator, self.unary())



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

            node = SyntaxNode("OPERADOR", operator)

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

            expression_node = self.expression()



            self.consume(

                TokenType.RPAREN,

                "Se esperaba ')' después de la expresión"

            )



            return expression_node



        raise SyntaxErrorCompiler(

            "Se esperaba un identificador, número, cadena, carácter o expresión entre paréntesis",

            token,

            "IDENTIFIER, INTEGER, REAL, STRING, CHAR o LPAREN"

        )



    def binary_node(

        self,

        left: SyntaxNode,

        operator: Token,

        right: SyntaxNode

    ) -> SyntaxNode:

        """

        Crea un nodo binario usando el operador como raíz.



        Ejemplo:

            y + 1



        Árbol:

            +

            ├── y <ID>

            └── 1 <INT>

        """



        node = SyntaxNode("OPERADOR", operator)

        node.add_child(left)

        node.add_child(right)

        return node