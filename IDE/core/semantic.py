from dataclasses import dataclass

from core.semantic_errors import SemanticErrorManager
from core.symbol_table import SymbolTable
from core.syntax_node import SyntaxNode
from core.token_type import TokenType


@dataclass
class SemanticResult:
    """Result produced by one independent semantic analysis."""

    annotated_ast: SyntaxNode
    symbol_table: SymbolTable
    errors: SemanticErrorManager


class SemanticAnalyzer:
    """Coordinates semantic analysis without modifying the parser AST."""

    NUMERIC_TYPES = {"int", "real"}
    ARITHMETIC_OPERATORS = {
        TokenType.PLUS,
        TokenType.MINUS,
        TokenType.STAR,
        TokenType.SLASH,
        TokenType.MODULO,
        TokenType.POWER,
    }
    ORDERING_OPERATORS = {
        TokenType.LESS,
        TokenType.LESS_EQUAL,
        TokenType.GREATER,
        TokenType.GREATER_EQUAL,
    }
    EQUALITY_OPERATORS = {TokenType.EQUAL, TokenType.NOT_EQUAL}
    LOGICAL_BINARY_OPERATORS = {TokenType.AND, TokenType.OR}
    UNARY_OPERATORS = {TokenType.PLUS, TokenType.MINUS, TokenType.NOT}
    UNKNOWN_VALUE = object()

    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors = SemanticErrorManager()

    def analyze(self, ast):
        """Clone, validate, and structurally visit a parser-generated AST."""

        self._reset_state()
        self._validate_ast(ast)

        annotated_ast = ast.clone()
        annotated_ast.clear_annotations()
        self.visit(annotated_ast)

        return SemanticResult(
            annotated_ast=annotated_ast,
            symbol_table=self.symbol_table,
            errors=self.errors,
        )

    def visit(self, node):
        """Dispatch a node to the semantic visitor implemented for its kind."""

        if not isinstance(node, SyntaxNode):
            raise TypeError("Semantic visitors require SyntaxNode instances")

        visitor = getattr(self, f"_visit_{node.name.lower()}", None)
        if visitor is None:
            return self._visit_unsupported(node)

        return visitor(node)

    def _reset_state(self):
        self.symbol_table = SymbolTable()
        self.errors = SemanticErrorManager()

    def _validate_ast(self, ast):
        if ast is None:
            raise ValueError("The AST cannot be None")

        if not isinstance(ast, SyntaxNode):
            raise TypeError("The AST root must be a SyntaxNode")

        if ast.name != "PROGRAMA":
            raise ValueError("The AST root must be a PROGRAMA node")

        pending = [ast]
        visited = set()

        while pending:
            node = pending.pop()
            node_id = id(node)

            if node_id in visited:
                raise ValueError(
                    "The AST must be a tree without cycles or shared nodes"
                )

            visited.add(node_id)

            if not isinstance(node.name, str) or not node.name:
                raise ValueError("Every AST node must have a non-empty name")

            if not isinstance(node.children, list):
                raise TypeError("Every AST node must contain a children list")

            for child in node.children:
                if not isinstance(child, SyntaxNode):
                    raise TypeError("Every AST child must be a SyntaxNode")

            pending.extend(node.children)

    def _visit_programa(self, node):
        self._mark_structural_node(node)
        self._visit_children(node)

    def _visit_main(self, node):
        self._mark_structural_node(node)
        self._visit_children(node)

    def _visit_bloque(self, node):
        scope = self.symbol_table.enter_scope()
        self._mark_structural_node(node, scope)

        try:
            self._visit_children(node)
        finally:
            self.symbol_table.exit_scope()

    def _visit_children(self, node):
        for child in node.children:
            self.visit(child)

    def _visit_condicion(self, node):
        return self.visit_condition(node)

    def visit_condition(self, node):
        """Validate that a control-flow condition has boolean type."""

        node.set_annotation("scope", self.symbol_table.current_scope())

        if len(node.children) != 1:
            node.set_annotation("semantic_status", "error")
            self.errors.add_error(
                error_type="invalid_condition",
                message="La condición no tiene la estructura esperada",
                line=node.get_line(),
                column=node.get_column(),
            )
            self._visit_children(node)
            return None

        expression = node.children[0]
        condition_type = self.visit(expression)

        if condition_type is None:
            self._mark_expression_failure(node)
            return None

        node.set_annotation("type", condition_type)

        if condition_type != "bool":
            node.set_annotation("semantic_status", "error")
            self.errors.invalid_condition(
                received_type=condition_type,
                line=expression.get_line(),
                column=expression.get_column(),
            )
            return None

        value = expression.get_annotation("value")
        if value is not None:
            node.set_annotation("value", value)

        node.set_annotation("semantic_status", "validated")
        return "bool"

    def _visit_then(self, node):
        return self._visit_control_container(node)

    def _visit_else(self, node):
        return self._visit_control_container(node)

    def _visit_cuerpo(self, node):
        return self._visit_control_container(node)

    def _visit_control_container(self, node):
        node.set_annotation("scope", self.symbol_table.current_scope())
        node.set_annotation("semantic_status", "validated")
        self._visit_children(node)
        self._propagate_child_status(node)

    def _visit_if(self, node):
        return self.visit_if(node)

    def visit_if(self, node):
        """Analyze all conditional branches from the same value state."""

        node.set_annotation("scope", self.symbol_table.current_scope())
        condition = self._find_child(node, "CONDICION")
        then_branch = self._find_child(node, "THEN")
        else_branch = self._find_child(node, "ELSE")

        if condition is None or then_branch is None:
            return self._invalid_control_structure(node, "if")

        self.visit(condition)
        baseline = self._snapshot_active_values()

        self.visit(then_branch)
        then_values = self._snapshot_active_values()

        self._restore_active_values(baseline)

        if else_branch is not None:
            self.visit(else_branch)
            else_values = self._snapshot_active_values()
        else:
            else_values = baseline

        self._merge_active_values(then_values, else_values)
        self._update_control_status(node)

    def _visit_while(self, node):
        return self.visit_while(node)

    def visit_while(self, node):
        """Analyze a pre-test loop without assuming that it executes."""

        node.set_annotation("scope", self.symbol_table.current_scope())
        condition = self._find_child(node, "CONDICION")
        body = self._find_body_child(node)

        if condition is None or body is None:
            return self._invalid_control_structure(node, "while")

        baseline = self._snapshot_active_values()
        self.visit(condition)
        condition_values = self._snapshot_active_values()
        self.visit(body)
        body_values = self._snapshot_active_values()

        self._merge_active_values(baseline, condition_values, body_values)
        self._update_control_status(node)

    def _visit_do_while(self, node):
        return self.visit_do_while(node)

    def visit_do_while(self, node):
        """Analyze a do-while body and its trailing condition."""

        return self._visit_post_test_loop(node, "do-while")

    def _visit_do_until(self, node):
        return self.visit_do_until(node)

    def visit_do_until(self, node):
        """Analyze a do-until body and its trailing condition."""

        return self._visit_post_test_loop(node, "do-until")

    def _visit_post_test_loop(self, node, structure_name):
        node.set_annotation("scope", self.symbol_table.current_scope())
        body = self._find_body_child(node)
        condition = self._find_child(node, "CONDICION")

        if body is None or condition is None:
            return self._invalid_control_structure(node, structure_name)

        baseline = self._snapshot_active_values()
        self.visit(body)
        body_values = self._snapshot_active_values()
        self.visit(condition)
        iteration_values = self._snapshot_active_values()

        self._merge_active_values(baseline, body_values, iteration_values)
        self._update_control_status(node)

    def _find_child(self, node, name):
        return next((child for child in node.children if child.name == name), None)

    def _find_body_child(self, node):
        return next(
            (child for child in node.children if child.name != "CONDICION"),
            None,
        )

    def _invalid_control_structure(self, node, structure_name):
        node.set_annotation("semantic_status", "error")
        self.errors.add_error(
            error_type="invalid_control_structure",
            message=f"La estructura '{structure_name}' no tiene la forma esperada",
            line=node.get_line(),
            column=node.get_column(),
        )
        self._visit_children(node)

    def _update_control_status(self, node):
        if any(self._has_error_node(child) for child in node.children):
            node.set_annotation("semantic_status", "error")
        elif any(self._has_pending_node(child) for child in node.children):
            node.set_annotation("semantic_status", "pending")
        else:
            node.set_annotation("semantic_status", "validated")

    def _visit_cin(self, node):
        return self.visit_input(node)

    def visit_input(self, node):
        """Resolve input targets and invalidate only their known values."""

        node.set_annotation("scope", self.symbol_table.current_scope())
        node.set_annotation("semantic_status", "validated")

        for target in node.children:
            if target.name != "IDENTIFICADOR":
                self.visit(target)
                node.set_annotation("semantic_status", "error")
                self.errors.add_error(
                    error_type="invalid_input_target",
                    message="La entrada requiere un identificador modificable",
                    line=target.get_line(),
                    column=target.get_column(),
                )
                continue

            target_type = self.visit_identifier(target)
            if target_type is None:
                node.set_annotation("semantic_status", "error")
                continue

            symbol = self.symbol_table.lookup(target.get_token_value())
            if symbol is not None:
                symbol.value = None
            target.set_annotation("value", None)

        self._propagate_child_status(node)

    def _visit_cout(self, node):
        return self.visit_output(node)

    def visit_output(self, node):
        """Analyze output expressions without changing their symbol values."""

        node.set_annotation("scope", self.symbol_table.current_scope())
        node.set_annotation("semantic_status", "validated")

        for expression in node.children:
            self.visit(expression)

        self._propagate_child_status(node)

    def _visit_llamar(self, node):
        return self.visit_function_call(node)

    def visit_function_call(self, node):
        """Analyze call arguments while keeping the unknown signature explicit."""

        node.set_annotation("scope", self.symbol_table.current_scope())
        node.set_annotation("semantic_status", "unsupported")

        callee = node.children[0] if node.children else None
        if callee is not None:
            callee.set_annotation("scope", self.symbol_table.current_scope())
            callee.set_annotation("semantic_status", "unsupported")

            for argument in node.children[1:]:
                self.visit(argument)

        self.errors.add_error(
            error_type="unsupported_node",
            message=(
                "La llamada a función no puede validarse sin información "
                "de firmas"
            ),
            line=node.get_line() or (callee.get_line() if callee else None),
            column=node.get_column() or (callee.get_column() if callee else None),
        )

        if any(self._has_error_node(child) for child in node.children[1:]):
            node.set_annotation("semantic_status", "error")

        self._invalidate_active_values()
        return None

    def _visit_declarar(self, node):
        return self.visit_declaration(node)

    def visit_declaration(self, node):
        """Declare every identifier represented by a DECLARAR node."""

        declared_type = self._declaration_type(node)
        node.set_annotation("scope", self.symbol_table.current_scope())

        if declared_type is None:
            node.set_annotation("semantic_status", "error")
            self.errors.add_error(
                error_type="invalid_declaration",
                message="La declaración no contiene un tipo soportado",
                line=node.get_line(),
                column=node.get_column(),
            )
            return None

        node.set_annotation("type", declared_type)
        node.set_annotation("semantic_status", "validated")

        for declarator in node.children:
            if declarator.name == "IDENTIFICADOR":
                self._declare_identifier(declarator, declared_type)
                continue

            if self._is_assignment(declarator):
                self._visit_declaration_assignment(declarator, declared_type)
                continue

            self.visit(declarator)

        self._propagate_child_status(node)
        return declared_type

    def _visit_declaration_assignment(self, node, declared_type):
        if len(node.children) != 2 or node.children[0].name != "IDENTIFICADOR":
            return self.visit_assignment(node)

        target = node.children[0]
        symbol = self._declare_identifier(target, declared_type)
        return self.visit_assignment(
            node,
            target_symbol=symbol,
            declaration_target=True,
        )

    def _declare_identifier(self, node, declared_type):
        name = node.get_token_value()
        scope = self.symbol_table.current_scope()

        node.set_annotation("type", declared_type)
        node.set_annotation("scope", scope)

        if not name:
            node.set_annotation("semantic_status", "error")
            self.errors.add_error(
                error_type="invalid_declaration",
                message="La declaración contiene un identificador inválido",
                line=node.get_line(),
                column=node.get_column(),
            )
            return None

        if self.symbol_table.exists(name, current_scope_only=True):
            node.set_annotation("semantic_status", "error")
            self.errors.duplicate_identifier(
                name=name,
                scope=scope,
                line=node.get_line(),
                column=node.get_column(),
            )
            return None

        symbol = self.symbol_table.insert(
            name=name,
            data_type=declared_type,
            line=node.get_line(),
        )
        node.set_annotation("semantic_status", "validated")
        node.set_annotation("address", symbol.address)
        return symbol

    def _visit_identificador(self, node):
        return self.visit_identifier(node)

    def visit_identifier(self, node):
        """Resolve an identifier and register its source occurrence."""

        name = node.get_token_value()
        symbol = self.symbol_table.lookup(name)

        if symbol is None:
            node.set_annotation("semantic_status", "error")
            node.set_annotation("scope", self.symbol_table.current_scope())
            self.errors.undeclared_identifier(
                name=name,
                line=node.get_line(),
                column=node.get_column(),
            )
            return None

        self.symbol_table.add_usage(name, node.get_line())
        node.set_annotation("type", symbol.data_type)
        node.set_annotation("scope", symbol.scope)
        node.set_annotation("address", symbol.address)
        node.set_annotation("semantic_status", "validated")

        if symbol.value is not None:
            node.set_annotation("value", symbol.value)

        return symbol.data_type

    def _visit_numero(self, node):
        return self.visit_literal(node)

    def _visit_cadena(self, node):
        return self.visit_literal(node)

    def _visit_caracter(self, node):
        return self.visit_literal(node)

    def visit_literal(self, node):
        """Annotate a literal with its semantic type and safe Python value."""

        token_type = node.get_token_type()
        literal_types = {
            TokenType.INTEGER: "int",
            TokenType.REAL: "real",
            TokenType.STRING: "string",
            TokenType.CHAR: "char",
        }
        semantic_type = literal_types.get(token_type)

        if semantic_type is None:
            node.set_annotation("semantic_status", "error")
            self.errors.add_error(
                error_type="invalid_literal",
                message=f"El nodo '{node.name}' no contiene un literal válido",
                line=node.get_line(),
                column=node.get_column(),
            )
            return None

        try:
            value = self._literal_value(node.get_token_value(), token_type)
        except (TypeError, ValueError):
            node.set_annotation("semantic_status", "error")
            self.errors.add_error(
                error_type="invalid_literal",
                message=f"El literal '{node.get_token_value()}' no es válido",
                line=node.get_line(),
                column=node.get_column(),
            )
            return None

        node.set_annotation("type", semantic_type)
        node.set_annotation("value", value)
        node.set_annotation("scope", self.symbol_table.current_scope())
        node.set_annotation("semantic_status", "validated")
        return semantic_type

    def _visit_operador(self, node):
        if self._is_assignment(node):
            return self.visit_assignment(node)

        token_type = node.get_token_type()

        if token_type in {TokenType.INCREMENT, TokenType.DECREMENT}:
            return self.visit_update_expression(node)

        if token_type in (
            self.ARITHMETIC_OPERATORS
            | self.ORDERING_OPERATORS
            | self.EQUALITY_OPERATORS
            | self.LOGICAL_BINARY_OPERATORS
        ) and len(node.children) == 2:
            return self.visit_binary_expression(node)

        if token_type in self.UNARY_OPERATORS and len(node.children) == 1:
            return self.visit_unary_expression(node)

        return self._visit_unsupported(node)

    def visit_binary_expression(self, node):
        """Infer the type and constant value of a binary expression."""

        node.set_annotation("scope", self.symbol_table.current_scope())

        if len(node.children) != 2:
            return self._invalid_expression_structure(node, "binaria")

        left, right = node.children
        token_type = node.get_token_type()
        left_type = self.visit(left)

        state_before_right = None
        if token_type in self.LOGICAL_BINARY_OPERATORS:
            state_before_right = self._snapshot_active_values()

        right_type = self.visit(right)

        if state_before_right is not None:
            state_after_right = self._snapshot_active_values()
            self._apply_logical_side_effects(
                token_type,
                left,
                state_before_right,
                state_after_right,
            )

        if left_type is None or right_type is None:
            self._mark_expression_failure(node)
            return None

        if token_type in self.ARITHMETIC_OPERATORS:
            result_type = self._arithmetic_result_type(
                node,
                left,
                left_type,
                right,
                right_type,
            )
        elif token_type in self.ORDERING_OPERATORS:
            result_type = self._ordering_result_type(
                node,
                left,
                left_type,
                right,
                right_type,
            )
        elif token_type in self.EQUALITY_OPERATORS:
            result_type = self._equality_result_type(
                node,
                left,
                left_type,
                right,
                right_type,
            )
        elif token_type in self.LOGICAL_BINARY_OPERATORS:
            result_type = self._logical_result_type(
                node,
                left_type,
                right_type,
            )
        else:
            return self._visit_unsupported(node)

        if result_type is None:
            return None

        node.set_annotation("type", result_type)
        node.set_annotation("semantic_status", "validated")

        value = self._evaluate_binary_expression(node, left, right)
        if node.get_annotation("semantic_status") == "error":
            return None

        if value is not self.UNKNOWN_VALUE:
            node.set_annotation("value", value)

        return result_type

    def _apply_logical_side_effects(
        self,
        token_type,
        left,
        state_before_right,
        state_after_right,
    ):
        """Apply RHS effects only on execution paths that evaluate the RHS."""

        left_value = left.get_annotation("value")
        skips_right = (
            token_type == TokenType.AND and left_value is False
        ) or (
            token_type == TokenType.OR and left_value is True
        )
        executes_right = (
            token_type == TokenType.AND and left_value is True
        ) or (
            token_type == TokenType.OR and left_value is False
        )

        if skips_right:
            self._restore_active_values(state_before_right)
        elif not executes_right:
            self._merge_active_values(state_before_right, state_after_right)

    def visit_unary_expression(self, node):
        """Infer the type and constant value of a supported unary expression."""

        node.set_annotation("scope", self.symbol_table.current_scope())

        if len(node.children) != 1:
            return self._invalid_expression_structure(node, "unaria")

        operand = node.children[0]
        operand_type = self.visit(operand)

        if operand_type is None:
            self._mark_expression_failure(node)
            return None

        token_type = node.get_token_type()

        if token_type in {TokenType.PLUS, TokenType.MINUS}:
            if operand_type not in self.NUMERIC_TYPES:
                return self._invalid_operator(node, operand_type)
            result_type = operand_type
        elif token_type == TokenType.NOT:
            if operand_type != "bool":
                return self._invalid_operator(node, operand_type)
            result_type = "bool"
        else:
            return self._visit_unsupported(node)

        node.set_annotation("type", result_type)
        node.set_annotation("semantic_status", "validated")

        value = operand.get_annotation("value")
        if value is not None:
            try:
                if token_type == TokenType.PLUS:
                    value = +value
                elif token_type == TokenType.MINUS:
                    value = -value
                else:
                    value = not value
                node.set_annotation("value", value)
            except (ArithmeticError, TypeError, ValueError):
                self._constant_evaluation_error(node)
                return None

        return result_type

    def visit_update_expression(self, node):
        """Validate ++/-- and update only the referenced numeric symbol."""

        node.set_annotation("scope", self.symbol_table.current_scope())

        if len(node.children) != 1:
            return self._invalid_expression_structure(node, "de incremento")

        operand = node.children[0]
        if operand.name != "IDENTIFICADOR":
            self.visit(operand)
            node.set_annotation("semantic_status", "error")
            self.errors.add_error(
                error_type="invalid_increment_target",
                message="El incremento o decremento requiere un identificador",
                line=node.get_line(),
                column=node.get_column(),
            )
            return None

        operand_type = self.visit_identifier(operand)
        if operand_type is None:
            node.set_annotation("semantic_status", "error")
            return None

        if operand_type not in self.NUMERIC_TYPES:
            return self._invalid_operator(node, operand_type)

        symbol = self.symbol_table.lookup(operand.get_token_value())
        old_value = symbol.value if symbol is not None else None
        new_value = None

        if old_value is not None:
            try:
                delta = 1 if node.get_token_type() == TokenType.INCREMENT else -1
                new_value = old_value + delta
            except (ArithmeticError, TypeError, ValueError, OverflowError):
                self._constant_evaluation_error(node)
                if symbol is not None:
                    symbol.value = None
                operand.set_annotation("value", None)
                return None

        if symbol is not None:
            symbol.value = new_value

        operand.set_annotation("value", new_value)
        node.set_annotation("type", operand_type)
        node.set_annotation("semantic_status", "validated")

        operator_form = self._update_operator_form(node, operand)
        node.set_annotation("operator_form", operator_form)
        expression_value = new_value if operator_form == "prefix" else old_value
        if expression_value is not None:
            node.set_annotation("value", expression_value)

        return operand_type

    def _update_operator_form(self, node, operand):
        """Recover prefix/postfix form from the parser-preserved positions."""

        operator_line = node.get_line()
        operand_line = operand.get_line()
        operator_column = node.get_column()
        operand_column = operand.get_column()

        if (
            operator_line is not None
            and operand_line is not None
            and operator_line > operand_line
        ):
            return "postfix"

        if operator_line == operand_line:
            if (
                operator_column is not None
                and operand_column is not None
                and operator_column > operand_column
            ):
                return "postfix"

        return "prefix"

    def visit_assignment(
        self,
        node,
        target_symbol=None,
        declaration_target=False,
    ):
        """Validate assignments whose right side already has a known type."""

        node.set_annotation("scope", self.symbol_table.current_scope())

        if len(node.children) != 2 or node.children[0].name != "IDENTIFICADOR":
            node.set_annotation("semantic_status", "error")
            self.errors.add_error(
                error_type="invalid_assignment",
                message="La asignación no tiene la estructura esperada",
                line=node.get_line(),
                column=node.get_column(),
            )
            self._visit_children(node)
            return None

        target, expression = node.children

        if declaration_target:
            target_type = target_symbol.data_type if target_symbol else None
        else:
            target_type = self.visit_identifier(target)
            target_symbol = self.symbol_table.lookup(target.get_token_value())

        expression_type = self.visit(expression)

        if target_symbol is not None:
            target_symbol.value = None
            target.set_annotation("value", None)

        if target_type is None:
            node.set_annotation("semantic_status", "error")
            return None

        if expression_type is None:
            if self._has_error_node(expression):
                node.set_annotation("semantic_status", "error")
            else:
                node.set_annotation(
                    "semantic_status",
                    "pending" if self._has_unsupported_node(expression) else "error",
                )
            return None

        node.set_annotation("type", target_type)

        if target_type == expression_type:
            assigned_value = expression.get_annotation("value")
        elif target_type == "real" and expression_type == "int":
            node.set_annotation("conversion", "int -> real")
            expression.set_annotation("conversion", "int -> real")
            assigned_value = expression.get_annotation("value")
            if assigned_value is not None:
                assigned_value = float(assigned_value)
        elif target_type == "int" and expression_type == "real":
            node.set_annotation("semantic_status", "error")
            self.errors.invalid_conversion(
                source_type=expression_type,
                target_type=target_type,
                line=node.get_line(),
                column=node.get_column(),
            )
            return None
        else:
            node.set_annotation("semantic_status", "error")
            self.errors.type_mismatch(
                expected_type=target_type,
                received_type=expression_type,
                line=node.get_line(),
                column=node.get_column(),
            )
            return None

        node.set_annotation("semantic_status", "validated")

        if assigned_value is not None:
            node.set_annotation("value", assigned_value)
            target.set_annotation("value", assigned_value)

        if target_symbol is not None:
            target_symbol.value = assigned_value

        return target_type

    def _arithmetic_result_type(
        self,
        node,
        left,
        left_type,
        right,
        right_type,
    ):
        if left_type not in self.NUMERIC_TYPES or right_type not in self.NUMERIC_TYPES:
            return self._invalid_operator(node, left_type, right_type)

        token_type = node.get_token_type()

        if token_type == TokenType.MODULO:
            if left_type != "int" or right_type != "int":
                return self._invalid_operator(node, left_type, right_type)
            return "int"

        if token_type == TokenType.SLASH:
            self._annotate_numeric_promotion(left, left_type)
            self._annotate_numeric_promotion(right, right_type)
            return "real"

        if "real" in {left_type, right_type}:
            self._annotate_numeric_promotion(left, left_type)
            self._annotate_numeric_promotion(right, right_type)
            return "real"

        return "int"

    def _ordering_result_type(
        self,
        node,
        left,
        left_type,
        right,
        right_type,
    ):
        if left_type not in self.NUMERIC_TYPES or right_type not in self.NUMERIC_TYPES:
            return self._invalid_operator(node, left_type, right_type)

        if "real" in {left_type, right_type}:
            self._annotate_numeric_promotion(left, left_type)
            self._annotate_numeric_promotion(right, right_type)

        return "bool"

    def _equality_result_type(
        self,
        node,
        left,
        left_type,
        right,
        right_type,
    ):
        if left_type in self.NUMERIC_TYPES and right_type in self.NUMERIC_TYPES:
            if "real" in {left_type, right_type}:
                self._annotate_numeric_promotion(left, left_type)
                self._annotate_numeric_promotion(right, right_type)
            return "bool"

        if left_type == right_type and left_type in {"bool", "string", "char"}:
            return "bool"

        return self._invalid_operator(node, left_type, right_type)

    def _logical_result_type(self, node, left_type, right_type):
        if left_type != "bool" or right_type != "bool":
            return self._invalid_operator(node, left_type, right_type)

        return "bool"

    def _evaluate_binary_expression(self, node, left, right):
        left_value = left.get_annotation("value")
        right_value = right.get_annotation("value")
        token_type = node.get_token_type()

        if token_type == TokenType.AND:
            if left_value is False or right_value is False:
                return False
            if left_value is None or right_value is None:
                return self.UNKNOWN_VALUE
            return left_value and right_value

        if token_type == TokenType.OR:
            if left_value is True or right_value is True:
                return True
            if left_value is None or right_value is None:
                return self.UNKNOWN_VALUE
            return left_value or right_value

        if token_type in {TokenType.SLASH, TokenType.MODULO} and right_value == 0:
            node.set_annotation("semantic_status", "error")
            self.errors.add_error(
                error_type="division_by_zero",
                message="División entre cero en una expresión constante",
                line=node.get_line(),
                column=node.get_column(),
            )
            return self.UNKNOWN_VALUE

        if (
            token_type == TokenType.POWER
            and node.get_annotation("type") == "int"
            and right_value is not None
            and right_value < 0
        ):
            node.set_annotation("semantic_status", "error")
            self.errors.add_error(
                error_type="invalid_exponent",
                message=(
                    "La potencia entera no admite exponentes negativos; "
                    "utiliza un operando real"
                ),
                line=node.get_line(),
                column=node.get_column(),
            )
            return self.UNKNOWN_VALUE

        if left_value is None or right_value is None:
            return self.UNKNOWN_VALUE

        operations = {
            TokenType.PLUS: lambda: left_value + right_value,
            TokenType.MINUS: lambda: left_value - right_value,
            TokenType.STAR: lambda: left_value * right_value,
            TokenType.SLASH: lambda: left_value / right_value,
            TokenType.MODULO: lambda: left_value % right_value,
            TokenType.POWER: lambda: left_value ** right_value,
            TokenType.LESS: lambda: left_value < right_value,
            TokenType.LESS_EQUAL: lambda: left_value <= right_value,
            TokenType.GREATER: lambda: left_value > right_value,
            TokenType.GREATER_EQUAL: lambda: left_value >= right_value,
            TokenType.EQUAL: lambda: left_value == right_value,
            TokenType.NOT_EQUAL: lambda: left_value != right_value,
        }

        try:
            value = operations[token_type]()
            if isinstance(value, complex):
                self._constant_evaluation_error(node)
                return self.UNKNOWN_VALUE
            return value
        except (ArithmeticError, TypeError, ValueError, OverflowError):
            self._constant_evaluation_error(node)
            return self.UNKNOWN_VALUE

    def _annotate_numeric_promotion(self, node, semantic_type):
        if semantic_type == "int":
            node.set_annotation("conversion", "int -> real")

    def _invalid_operator(self, node, left_type, right_type=None):
        node.set_annotation("semantic_status", "error")
        self.errors.invalid_operator(
            operator=node.get_token_value(),
            left_type=left_type,
            right_type=right_type,
            line=node.get_line(),
            column=node.get_column(),
        )
        return None

    def _invalid_expression_structure(self, node, expression_kind):
        node.set_annotation("semantic_status", "error")
        self.errors.add_error(
            error_type="invalid_expression",
            message=f"La expresión {expression_kind} no tiene la estructura esperada",
            line=node.get_line(),
            column=node.get_column(),
        )
        self._visit_children(node)
        return None

    def _mark_expression_failure(self, node):
        if self._has_error_node(node):
            node.set_annotation("semantic_status", "error")
        else:
            node.set_annotation(
                "semantic_status",
                "pending" if self._has_unsupported_node(node) else "error",
            )

    def _constant_evaluation_error(self, node):
        node.set_annotation("semantic_status", "error")
        self.errors.add_error(
            error_type="constant_evaluation_error",
            message="No se pudo evaluar la expresión constante de forma segura",
            line=node.get_line(),
            column=node.get_column(),
        )

    def _invalidate_active_values(self):
        for scope in self.symbol_table.scopes:
            for symbol in scope["symbols"].values():
                symbol.value = None

    def _snapshot_active_values(self):
        return {
            id(symbol): symbol.value
            for scope in self.symbol_table.scopes
            for symbol in scope["symbols"].values()
        }

    def _restore_active_values(self, values):
        for scope in self.symbol_table.scopes:
            for symbol in scope["symbols"].values():
                symbol.value = values.get(id(symbol))

    def _merge_active_values(self, *value_states):
        for scope in self.symbol_table.scopes:
            for symbol in scope["symbols"].values():
                possible_values = [
                    state.get(id(symbol))
                    for state in value_states
                ]
                first_value = possible_values[0]
                symbol.value = (
                    first_value
                    if all(value == first_value for value in possible_values[1:])
                    else None
                )

    def _declaration_type(self, node):
        declaration_types = {
            TokenType.INT: "int",
            TokenType.FLOAT: "real",
            TokenType.REAL_TYPE: "real",
        }
        return declaration_types.get(node.get_token_type())

    def _literal_value(self, lexeme, token_type):
        if token_type == TokenType.INTEGER:
            return int(lexeme)

        if token_type == TokenType.REAL:
            return float(lexeme)

        return lexeme

    def _is_assignment(self, node):
        return (
            isinstance(node, SyntaxNode)
            and node.name == "OPERADOR"
            and node.get_token_type() == TokenType.ASSIGN
        )

    def _has_unsupported_node(self, node):
        if node.get_annotation("semantic_status") == "unsupported":
            return True

        return any(self._has_unsupported_node(child) for child in node.children)

    def _has_error_node(self, node):
        if node.get_annotation("semantic_status") == "error":
            return True

        return any(self._has_error_node(child) for child in node.children)

    def _has_pending_node(self, node):
        if node.get_annotation("semantic_status") in {"pending", "unsupported"}:
            return True

        return any(self._has_pending_node(child) for child in node.children)

    def _propagate_child_status(self, node):
        statuses = {
            child.get_annotation("semantic_status")
            for child in node.children
        }

        if "error" in statuses:
            node.set_annotation("semantic_status", "error")
        elif "pending" in statuses or "unsupported" in statuses:
            node.set_annotation("semantic_status", "pending")

    def _mark_structural_node(self, node, scope=None):
        node.set_annotation("semantic_status", "structural")
        node.set_annotation(
            "scope",
            scope if scope is not None else self.symbol_table.current_scope(),
        )

    def _visit_unsupported(self, node):
        node.set_annotation("semantic_status", "unsupported")
        node.set_annotation("scope", self.symbol_table.current_scope())

        self.errors.add_error(
            error_type="unsupported_node",
            message=(
                f"El nodo '{node.name}' aún no tiene validación semántica"
            ),
            line=node.get_line(),
            column=node.get_column(),
        )

        self._visit_children(node)
