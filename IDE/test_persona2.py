import unittest

from core.lexer import Lexer
from core.parser import Parser
from core.semantic import SemanticAnalyzer, SemanticResult
from core.semantic_errors import SemanticErrorManager
from core.symbol_table import SymbolTable
from core.syntax_node import SyntaxNode
from core.token_model import Token
from core.token_type import TokenType


def make_structural_ast():
    program = SyntaxNode("PROGRAMA")
    main = SyntaxNode("MAIN")
    block = SyntaxNode("BLOQUE")
    nested_block = SyntaxNode("BLOQUE")

    block.add_child(nested_block)
    main.add_child(block)
    program.add_child(main)
    return program


def analyze_source(source):
    tokens, lexical_errors = Lexer(source).tokenize()
    if lexical_errors:
        raise AssertionError(f"Unexpected lexical errors: {lexical_errors}")

    ast = Parser(tokens).parse()
    return ast, SemanticAnalyzer().analyze(ast)


def find_nodes(root, name):
    matches = []
    pending = [root]

    while pending:
        node = pending.pop()
        if node.name == name:
            matches.append(node)
        pending.extend(reversed(node.children))

    return matches


def find_operators(root, token_type):
    return [
        node
        for node in find_nodes(root, "OPERADOR")
        if node.get_token_type() == token_type
    ]


class SemanticAnalyzerTests(unittest.TestCase):
    def test_analyzer_can_be_instantiated(self):
        analyzer = SemanticAnalyzer()

        self.assertIsInstance(analyzer.symbol_table, SymbolTable)
        self.assertIsInstance(analyzer.errors, SemanticErrorManager)

    def test_analyze_returns_compatible_result(self):
        result = SemanticAnalyzer().analyze(make_structural_ast())

        self.assertIsInstance(result, SemanticResult)
        self.assertIsInstance(result.annotated_ast, SyntaxNode)
        self.assertIsInstance(result.symbol_table, SymbolTable)
        self.assertIsInstance(result.errors, SemanticErrorManager)

    def test_accepts_ast_generated_by_existing_parser(self):
        tokens, lexical_errors = Lexer("main { }").tokenize()
        self.assertEqual(lexical_errors, [])

        ast = Parser(tokens).parse()
        result = SemanticAnalyzer().analyze(ast)

        self.assertEqual(result.annotated_ast.name, "PROGRAMA")
        self.assertEqual(
            result.annotated_ast.children[0].get_annotation("semantic_status"),
            "structural",
        )
        self.assertEqual(result.errors.count(), 0)

    def test_individual_and_multiple_declarations(self):
        _, result = analyze_source(
            "main {\n"
            "  int first;\n"
            "  float second;\n"
            "  real third;\n"
            "  int a, b, c;\n"
            "}"
        )
        symbols = result.symbol_table.get_all()

        self.assertEqual(
            [symbol["name"] for symbol in symbols],
            ["first", "second", "third", "a", "b", "c"],
        )
        self.assertEqual(
            [symbol["data_type"] for symbol in symbols],
            ["int", "real", "real", "int", "int", "int"],
        )
        self.assertEqual(
            [symbol["address"] for symbol in symbols],
            [0, 1, 2, 3, 4, 5],
        )
        self.assertEqual(
            [symbol["lines"] for symbol in symbols],
            [[2], [3], [4], [5], [5], [5]],
        )
        self.assertEqual(result.errors.count(), 0)

    def test_declared_and_undeclared_identifier_usage(self):
        _, result = analyze_source(
            "main {\n"
            "  int x;\n"
            "  x = x;\n"
            "  missing = x;\n"
            "}"
        )
        symbol = result.symbol_table.get_all()[0]
        errors = result.errors.get_objects()

        self.assertEqual(symbol["lines"], [2, 3, 4])
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].error_type, "undeclared_identifier")
        self.assertIn("missing", errors[0].message)

    def test_duplicate_declaration_in_same_scope(self):
        _, result = analyze_source("main { int value; real value; }")

        self.assertEqual(len(result.symbol_table.get_all()), 1)
        self.assertEqual(result.errors.count(), 1)
        self.assertEqual(
            result.errors.get_objects()[0].error_type,
            "duplicate_identifier",
        )

    def test_nested_scope_can_use_external_identifier(self):
        _, result = analyze_source(
            "main {\n"
            "  int outer = 1;\n"
            "  {\n"
            "    int inner;\n"
            "    inner = outer;\n"
            "  }\n"
            "}"
        )
        symbols = result.symbol_table.get_all()

        self.assertEqual([symbol["scope"] for symbol in symbols], ["scope_1", "scope_2"])
        self.assertEqual(symbols[0]["lines"], [2, 5])
        self.assertEqual(result.errors.count(), 0)

    def test_inner_declaration_shadows_external_identifier(self):
        _, result = analyze_source(
            "main {\n"
            "  int value;\n"
            "  {\n"
            "    real value;\n"
            "    value = 1.5;\n"
            "  }\n"
            "  value = 1;\n"
            "}"
        )
        symbols = result.symbol_table.get_all()

        self.assertEqual(len(symbols), 2)
        self.assertEqual([symbol["data_type"] for symbol in symbols], ["int", "real"])
        self.assertEqual([symbol["scope"] for symbol in symbols], ["scope_1", "scope_2"])
        self.assertEqual(symbols[0]["lines"], [2, 7])
        self.assertEqual(symbols[1]["lines"], [4, 5])
        self.assertEqual(result.errors.count(), 0)

    def test_literals_receive_types_and_values(self):
        _, result = analyze_source(
            'main { int i = 42; real r = 3.5; int s = "hello"; int c = \'z\'; }'
        )
        literals = {
            node.get_token_type(): node
            for name in ("NUMERO", "CADENA", "CARACTER")
            for node in find_nodes(result.annotated_ast, name)
        }

        self.assertEqual(literals[TokenType.INTEGER].get_annotation("type"), "int")
        self.assertEqual(literals[TokenType.INTEGER].get_annotation("value"), 42)
        self.assertEqual(literals[TokenType.REAL].get_annotation("type"), "real")
        self.assertEqual(literals[TokenType.REAL].get_annotation("value"), 3.5)
        self.assertEqual(literals[TokenType.STRING].get_annotation("type"), "string")
        self.assertEqual(literals[TokenType.STRING].get_annotation("value"), "hello")
        self.assertEqual(literals[TokenType.CHAR].get_annotation("type"), "char")
        self.assertEqual(literals[TokenType.CHAR].get_annotation("value"), "z")

    def test_valid_literal_and_identifier_assignments(self):
        _, result = analyze_source(
            "main { int a = 1; int b; b = a; real c = 2.5; float d = c; }"
        )
        symbols = result.symbol_table.get_all()

        self.assertEqual(result.errors.count(), 0)
        self.assertEqual(
            [symbol["value"] for symbol in symbols],
            [1, 1, 2.5, 2.5],
        )

    def test_real_to_int_assignment_reports_invalid_conversion(self):
        _, result = analyze_source("main { int value; value = 2.5; }")
        errors = result.errors.get_objects()

        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].error_type, "invalid_conversion")
        self.assertIn("'real'", errors[0].message)
        self.assertIn("'int'", errors[0].message)

    def test_assignment_to_undeclared_variable_has_no_secondary_type_error(self):
        _, result = analyze_source("main { missing = 1; }")
        error_types = [error.error_type for error in result.errors.get_objects()]

        self.assertEqual(error_types, ["undeclared_identifier"])

    def test_declarations_and_uses_have_type_annotations(self):
        _, result = analyze_source("main { float value; value = value; }")
        declaration = find_nodes(result.annotated_ast, "DECLARAR")[0]
        identifiers = find_nodes(result.annotated_ast, "IDENTIFICADOR")

        self.assertEqual(declaration.get_annotation("type"), "real")
        self.assertTrue(identifiers)
        self.assertTrue(
            all(node.get_annotation("type") == "real" for node in identifiers)
        )

    def test_unsupported_expression_is_pending_without_false_type_error(self):
        _, result = analyze_source("main { int value; value = mystery(); }")
        assignments = [
            node
            for node in find_nodes(result.annotated_ast, "OPERADOR")
            if node.get_token_type() == TokenType.ASSIGN
        ]
        error_types = [error.error_type for error in result.errors.get_objects()]

        self.assertEqual(assignments[0].get_annotation("semantic_status"), "pending")
        self.assertEqual(error_types, ["unsupported_node"])

    def test_invalid_target_is_not_hidden_by_unsupported_expression(self):
        _, result = analyze_source("main { missing = mystery(); }")
        assignment = [
            node
            for node in find_nodes(result.annotated_ast, "OPERADOR")
            if node.get_token_type() == TokenType.ASSIGN
        ][0]
        error_types = [error.error_type for error in result.errors.get_objects()]

        self.assertEqual(assignment.get_annotation("semantic_status"), "error")
        self.assertEqual(
            error_types,
            ["undeclared_identifier", "unsupported_node"],
        )

    def test_integer_arithmetic_and_parser_precedence(self):
        _, result = analyze_source("main { int result = 5 + 3 * 2; }")
        addition = find_operators(result.annotated_ast, TokenType.PLUS)[0]
        multiplication = find_operators(result.annotated_ast, TokenType.STAR)[0]

        self.assertEqual(result.errors.count(), 0)
        self.assertEqual(addition.get_annotation("type"), "int")
        self.assertEqual(addition.get_annotation("value"), 11)
        self.assertEqual(multiplication.get_annotation("value"), 6)
        self.assertEqual(result.symbol_table.get_all()[0]["value"], 11)

    def test_real_and_mixed_arithmetic(self):
        _, result = analyze_source(
            "main { real first = 1.5 + 2.5 * 2.0; real second = 1 + 2.5; }"
        )
        additions = find_operators(result.annotated_ast, TokenType.PLUS)
        integer = [
            node
            for node in find_nodes(result.annotated_ast, "NUMERO")
            if node.get_token_type() == TokenType.INTEGER
        ][0]

        self.assertEqual(result.errors.count(), 0)
        self.assertEqual([node.get_annotation("type") for node in additions], ["real", "real"])
        self.assertEqual([node.get_annotation("value") for node in additions], [6.5, 3.5])
        self.assertEqual(integer.get_annotation("conversion"), "int -> real")

    def test_integer_division_produces_real_and_records_promotions(self):
        _, result = analyze_source("main { real result = 5 / 2; }")
        division = find_operators(result.annotated_ast, TokenType.SLASH)[0]

        self.assertEqual(result.errors.count(), 0)
        self.assertEqual(division.get_annotation("type"), "real")
        self.assertEqual(division.get_annotation("value"), 2.5)
        self.assertTrue(
            all(
                child.get_annotation("conversion") == "int -> real"
                for child in division.children
            )
        )

    def test_integer_modulo_and_power_are_constant(self):
        _, result = analyze_source(
            "main { int remainder = 5 % 2; int power = 2 ^ 3; }"
        )
        modulo = find_operators(result.annotated_ast, TokenType.MODULO)[0]
        power = find_operators(result.annotated_ast, TokenType.POWER)[0]

        self.assertEqual(result.errors.count(), 0)
        self.assertEqual(modulo.get_annotation("type"), "int")
        self.assertEqual(modulo.get_annotation("value"), 1)
        self.assertEqual(power.get_annotation("type"), "int")
        self.assertEqual(power.get_annotation("value"), 8)

    def test_negative_integer_exponent_is_rejected_safely(self):
        _, result = analyze_source("main { int result = 2 ^ -1; }")
        power = find_operators(result.annotated_ast, TokenType.POWER)[0]

        self.assertEqual(power.get_annotation("semantic_status"), "error")
        self.assertIsNone(power.get_annotation("value"))
        self.assertEqual(
            [error.error_type for error in result.errors.get_objects()],
            ["invalid_exponent"],
        )

    def test_int_to_real_assignment_conversion(self):
        _, result = analyze_source("main { real value = 1; }")
        assignment = find_operators(result.annotated_ast, TokenType.ASSIGN)[0]
        integer = find_nodes(result.annotated_ast, "NUMERO")[0]
        symbol = result.symbol_table.get_all()[0]

        self.assertEqual(result.errors.count(), 0)
        self.assertEqual(assignment.get_annotation("conversion"), "int -> real")
        self.assertEqual(integer.get_annotation("conversion"), "int -> real")
        self.assertEqual(assignment.get_annotation("value"), 1.0)
        self.assertEqual(symbol["value"], 1.0)

    def test_nested_relational_and_logical_expressions(self):
        _, result = analyze_source(
            "main { int result = (1 < 2) && !(3 == 4); }"
        )
        logical_and = find_operators(result.annotated_ast, TokenType.AND)[0]
        logical_not = find_operators(result.annotated_ast, TokenType.NOT)[0]
        less = find_operators(result.annotated_ast, TokenType.LESS)[0]
        equal = find_operators(result.annotated_ast, TokenType.EQUAL)[0]

        self.assertEqual(logical_and.get_annotation("type"), "bool")
        self.assertEqual(logical_and.get_annotation("value"), True)
        self.assertEqual(logical_not.get_annotation("value"), True)
        self.assertEqual(less.get_annotation("value"), True)
        self.assertEqual(equal.get_annotation("value"), False)
        self.assertEqual(
            [error.error_type for error in result.errors.get_objects()],
            ["type_mismatch"],
        )

    def test_mixed_numeric_comparison_records_promotion(self):
        _, result = analyze_source("main { int result = 1 < 2.5; }")
        comparison = find_operators(result.annotated_ast, TokenType.LESS)[0]
        integer = comparison.children[0]

        self.assertEqual(comparison.get_annotation("type"), "bool")
        self.assertEqual(comparison.get_annotation("value"), True)
        self.assertEqual(integer.get_annotation("conversion"), "int -> real")

    def test_string_equality_is_supported(self):
        _, result = analyze_source('main { int result = "same" == "same"; }')
        equality = find_operators(result.annotated_ast, TokenType.EQUAL)[0]

        self.assertEqual(equality.get_annotation("type"), "bool")
        self.assertEqual(equality.get_annotation("value"), True)
        self.assertNotIn(
            "invalid_operator",
            [error.error_type for error in result.errors.get_objects()],
        )

    def test_numeric_unary_operators(self):
        _, result = analyze_source("main { int negative = -5; real positive = +2.5; }")
        minus = find_operators(result.annotated_ast, TokenType.MINUS)[0]
        plus = find_operators(result.annotated_ast, TokenType.PLUS)[0]

        self.assertEqual(result.errors.count(), 0)
        self.assertEqual(minus.get_annotation("type"), "int")
        self.assertEqual(minus.get_annotation("value"), -5)
        self.assertEqual(plus.get_annotation("type"), "real")
        self.assertEqual(plus.get_annotation("value"), 2.5)

    def test_division_by_zero_is_reported_without_secondary_error(self):
        _, result = analyze_source("main { real result = 10 / 0; }")
        division = find_operators(result.annotated_ast, TokenType.SLASH)[0]

        self.assertEqual(division.get_annotation("semantic_status"), "error")
        self.assertIsNone(division.get_annotation("value"))
        self.assertEqual(
            [error.error_type for error in result.errors.get_objects()],
            ["division_by_zero"],
        )
        self.assertIsNone(result.symbol_table.get_all()[0]["value"])

    def test_unknown_identifier_value_does_not_fake_constant_result(self):
        _, result = analyze_source("main { int source; int result = source + 1; }")
        addition = find_operators(result.annotated_ast, TokenType.PLUS)[0]
        symbols = result.symbol_table.get_all()

        self.assertEqual(result.errors.count(), 0)
        self.assertEqual(addition.get_annotation("type"), "int")
        self.assertIsNone(addition.get_annotation("value"))
        self.assertIsNone(symbols[1]["value"])

    def test_incompatible_arithmetic_operator_has_no_secondary_assignment_error(self):
        _, result = analyze_source('main { int result = "text" + 1; }')
        addition = find_operators(result.annotated_ast, TokenType.PLUS)[0]

        self.assertEqual(addition.get_annotation("semantic_status"), "error")
        self.assertEqual(
            [error.error_type for error in result.errors.get_objects()],
            ["invalid_operator"],
        )

    def test_integer_operands_are_not_accepted_as_booleans(self):
        _, result = analyze_source("main { int result = 1 && 2; }")

        self.assertEqual(
            [error.error_type for error in result.errors.get_objects()],
            ["invalid_operator"],
        )

    def test_undeclared_operand_does_not_create_operator_or_assignment_errors(self):
        _, result = analyze_source("main { int result = missing + 1; }")
        addition = find_operators(result.annotated_ast, TokenType.PLUS)[0]

        self.assertEqual(addition.get_annotation("semantic_status"), "error")
        self.assertEqual(
            [error.error_type for error in result.errors.get_objects()],
            ["undeclared_identifier"],
        )

    def test_error_status_takes_priority_over_pending_operand(self):
        _, result = analyze_source("main { int result = missing + mystery(1); }")
        assignment = find_operators(result.annotated_ast, TokenType.ASSIGN)[0]
        addition = find_operators(result.annotated_ast, TokenType.PLUS)[0]

        self.assertEqual(addition.get_annotation("semantic_status"), "error")
        self.assertEqual(assignment.get_annotation("semantic_status"), "error")
        self.assertEqual(
            [error.error_type for error in result.errors.get_objects()],
            ["undeclared_identifier", "unsupported_node"],
        )

    def test_pending_function_call_does_not_treat_callee_as_variable(self):
        _, result = analyze_source("main { int result = mystery(1) + 2; }")
        addition = find_operators(result.annotated_ast, TokenType.PLUS)[0]
        error_types = [error.error_type for error in result.errors.get_objects()]

        self.assertEqual(addition.get_annotation("semantic_status"), "pending")
        self.assertEqual(error_types, ["unsupported_node"])

    def test_values_are_invalidated_after_control_flow(self):
        _, result = analyze_source(
            "main { int value = 1; if (value > 0) { value = 2; } "
            "int derived = value + 1; }"
        )
        symbols = result.symbol_table.get_all()

        self.assertIsNone(symbols[0]["value"])
        self.assertIsNone(symbols[1]["value"])
        self.assertEqual(result.errors.count(), 0)

    def test_increment_updates_known_values(self):
        _, result = analyze_source(
            "main { int value = 1; value++; int derived = value + 1; }"
        )
        symbols = result.symbol_table.get_all()

        self.assertEqual(symbols[0]["value"], 2)
        self.assertEqual(symbols[1]["value"], 3)
        self.assertEqual(result.errors.count(), 0)

    def test_if_with_valid_boolean_condition(self):
        _, result = analyze_source(
            "main { int value = 1; if (value > 0) { int local = 2; } }"
        )
        if_node = find_nodes(result.annotated_ast, "IF")[0]
        condition = find_nodes(if_node, "CONDICION")[0]

        self.assertEqual(result.errors.count(), 0)
        self.assertEqual(if_node.get_annotation("semantic_status"), "validated")
        self.assertEqual(condition.get_annotation("type"), "bool")
        self.assertEqual(condition.get_annotation("value"), True)

    def test_if_rejects_numeric_condition(self):
        _, result = analyze_source("main { if (10) { int local; } }")
        condition = find_nodes(result.annotated_ast, "CONDICION")[0]

        self.assertEqual(condition.get_annotation("semantic_status"), "error")
        self.assertEqual(
            [error.error_type for error in result.errors.get_objects()],
            ["invalid_condition"],
        )

    def test_if_else_divergent_values_become_unknown(self):
        _, result = analyze_source(
            "main { int value = 0; if (1 < 2) { value = 1; } "
            "else { value = 2; } int derived = value + 1; }"
        )
        symbols = result.symbol_table.get_all()

        self.assertEqual(result.errors.count(), 0)
        self.assertIsNone(symbols[0]["value"])
        self.assertIsNone(symbols[1]["value"])

    def test_if_else_equal_values_are_preserved(self):
        _, result = analyze_source(
            "main { int value = 0; if (1 < 2) { value = 2; } "
            "else { value = 2; } int derived = value + 1; }"
        )
        symbols = result.symbol_table.get_all()

        self.assertEqual(result.errors.count(), 0)
        self.assertEqual(symbols[0]["value"], 2)
        self.assertEqual(symbols[1]["value"], 3)

    def test_else_if_is_analyzed_without_unsupported_nodes(self):
        _, result = analyze_source(
            "main { int value = 0; if (value > 0) { value = 1; } "
            "else if (value < 0) { value = -1; } else { value = 2; } }"
        )
        if_nodes = find_nodes(result.annotated_ast, "IF")

        self.assertEqual(len(if_nodes), 2)
        self.assertEqual(result.errors.count(), 0)
        self.assertTrue(
            all(node.get_annotation("semantic_status") == "validated" for node in if_nodes)
        )
        self.assertIsNone(result.symbol_table.get_all()[0]["value"])

    def test_nested_if_structures_are_analyzed(self):
        _, result = analyze_source(
            "main { int value = 1; if (value > 0) { "
            "if (value < 10) { value = 2; } } }"
        )

        self.assertEqual(len(find_nodes(result.annotated_ast, "IF")), 2)
        self.assertEqual(result.errors.count(), 0)
        self.assertIsNone(result.symbol_table.get_all()[0]["value"])

    def test_if_then_else_end_uses_current_scope(self):
        _, result = analyze_source(
            "main { if (1 < 2) then int then_value = 1; "
            "else int else_value = 2; end; }"
        )
        symbols = result.symbol_table.get_all()
        then_node = find_nodes(result.annotated_ast, "THEN")[0]
        else_node = find_nodes(result.annotated_ast, "ELSE")[0]

        self.assertEqual(result.errors.count(), 0)
        self.assertEqual([symbol["scope"] for symbol in symbols], ["scope_1", "scope_1"])
        self.assertEqual(then_node.get_annotation("scope"), "scope_1")
        self.assertEqual(else_node.get_annotation("scope"), "scope_1")

    def test_while_with_braces_and_valid_condition(self):
        _, result = analyze_source(
            "main { int value = 0; while (value < 3) { value = value + 1; } }"
        )
        while_node = find_nodes(result.annotated_ast, "WHILE")[0]

        self.assertEqual(result.errors.count(), 0)
        self.assertEqual(while_node.get_annotation("semantic_status"), "validated")
        self.assertIsNone(result.symbol_table.get_all()[0]["value"])

    def test_while_rejects_non_boolean_condition(self):
        _, result = analyze_source("main { while (1) { int local; } }")

        self.assertEqual(
            [error.error_type for error in result.errors.get_objects()],
            ["invalid_condition"],
        )
        self.assertEqual(
            find_nodes(result.annotated_ast, "WHILE")[0].get_annotation(
                "semantic_status"
            ),
            "error",
        )

    def test_while_do_end_variant_is_supported(self):
        _, result = analyze_source(
            "main { int value = 0; while value < 3 do value = value + 1; end; }"
        )
        body = find_nodes(result.annotated_ast, "CUERPO")[0]

        self.assertEqual(result.errors.count(), 0)
        self.assertEqual(body.get_annotation("semantic_status"), "validated")
        self.assertEqual(body.get_annotation("scope"), "scope_1")
        self.assertIsNone(result.symbol_table.get_all()[0]["value"])

    def test_while_with_single_statement_body_is_supported(self):
        _, result = analyze_source(
            "main { int value = 0; while (value < 3) value = value + 1; }"
        )

        self.assertEqual(result.errors.count(), 0)
        self.assertEqual(
            find_nodes(result.annotated_ast, "WHILE")[0].get_annotation(
                "semantic_status"
            ),
            "validated",
        )

    def test_do_while_is_supported(self):
        _, result = analyze_source(
            "main { int value = 0; do { value = value + 1; } "
            "while (value < 3); }"
        )
        loop = find_nodes(result.annotated_ast, "DO_WHILE")[0]

        self.assertEqual(result.errors.count(), 0)
        self.assertEqual(loop.get_annotation("semantic_status"), "validated")
        self.assertIsNone(result.symbol_table.get_all()[0]["value"])

    def test_do_until_without_braces_is_supported(self):
        _, result = analyze_source(
            "main { int value = 0; do value = value + 1; until (value == 3); }"
        )
        loop = find_nodes(result.annotated_ast, "DO_UNTIL")[0]
        body_block = find_nodes(loop, "BLOQUE")[0]

        self.assertEqual(result.errors.count(), 0)
        self.assertEqual(loop.get_annotation("semantic_status"), "validated")
        self.assertEqual(body_block.get_annotation("scope"), "scope_2")
        self.assertIsNone(result.symbol_table.get_all()[0]["value"])

    def test_compound_logical_condition_is_valid(self):
        _, result = analyze_source(
            "main { int value = 5; if ((value > 0) && (value < 10)) "
            "{ int local; } }"
        )
        condition = find_nodes(result.annotated_ast, "CONDICION")[0]

        self.assertEqual(result.errors.count(), 0)
        self.assertEqual(condition.get_annotation("type"), "bool")
        self.assertEqual(condition.get_annotation("value"), True)

    def test_undeclared_identifier_in_condition_has_no_secondary_error(self):
        _, result = analyze_source("main { if (missing > 0) { int local; } }")

        self.assertEqual(
            [error.error_type for error in result.errors.get_objects()],
            ["undeclared_identifier"],
        )

    def test_semantic_error_inside_branch_is_reported(self):
        _, result = analyze_source("main { if (1 < 2) { missing = 1; } }")
        if_node = find_nodes(result.annotated_ast, "IF")[0]

        self.assertEqual(
            [error.error_type for error in result.errors.get_objects()],
            ["undeclared_identifier"],
        )
        self.assertEqual(if_node.get_annotation("semantic_status"), "error")

    def test_braced_branch_declaration_uses_inner_scope(self):
        _, result = analyze_source(
            "main { int outer = 1; if (outer > 0) { int local = 2; } }"
        )
        symbols = result.symbol_table.get_all()

        self.assertEqual([symbol["scope"] for symbol in symbols], ["scope_1", "scope_2"])
        self.assertEqual(result.errors.count(), 0)

    def test_else_branch_starts_from_pre_if_value_state(self):
        _, result = analyze_source(
            "main { int value = 1; if (value > 0) { value = 2; } "
            "else { int observed = value + 1; } }"
        )
        symbols = result.symbol_table.get_all()
        observed = next(symbol for symbol in symbols if symbol["name"] == "observed")

        self.assertEqual(observed["value"], 2)
        self.assertIsNone(symbols[0]["value"])
        self.assertEqual(result.errors.count(), 0)

    def test_loop_changes_do_not_feed_constant_expression_after_loop(self):
        _, result = analyze_source(
            "main { int value = 1; while (value < 3) { value = value + 1; } "
            "int derived = value * 2; }"
        )
        symbols = result.symbol_table.get_all()

        self.assertIsNone(symbols[0]["value"])
        self.assertIsNone(symbols[1]["value"])
        self.assertEqual(result.errors.count(), 0)

    def test_control_flow_analysis_preserves_original_ast(self):
        tokens, lexical_errors = Lexer(
            "main { int value = 0; if (value > 0) { value = 1; } "
            "else { value = 2; } }"
        ).tokenize()
        self.assertEqual(lexical_errors, [])
        ast = Parser(tokens).parse()
        original = ast.to_semantic_dict()

        SemanticAnalyzer().analyze(ast)

        self.assertEqual(ast.to_semantic_dict(), original)

    def test_parenthesized_input_resolves_and_invalidates_target(self):
        _, result = analyze_source(
            "main {\n  int value = 7;\n  cin(value);\n}"
        )
        input_node = find_nodes(result.annotated_ast, "CIN")[0]
        target = input_node.children[0]
        symbol = result.symbol_table.get_all()[0]

        self.assertEqual(result.errors.count(), 0)
        self.assertEqual(input_node.get_annotation("semantic_status"), "validated")
        self.assertEqual(target.get_annotation("type"), "int")
        self.assertEqual(symbol["lines"], [2, 3])
        self.assertIsNone(symbol["value"])

    def test_parenthesized_input_invalidates_only_its_targets(self):
        _, result = analyze_source(
            "main { int first = 1; int second = 2; int untouched = 3; "
            "cin(first, second); }"
        )
        symbols = result.symbol_table.get_all()

        self.assertEqual([symbol["value"] for symbol in symbols], [None, None, 3])
        self.assertEqual(result.errors.count(), 0)

    def test_shift_input_supports_multiple_targets(self):
        _, result = analyze_source(
            "main { int first = 1; real second = 2.5; "
            "cin >> first >> second; }"
        )
        input_node = find_nodes(result.annotated_ast, "CIN")[0]
        symbols = result.symbol_table.get_all()

        self.assertEqual(
            [child.get_annotation("type") for child in input_node.children],
            ["int", "real"],
        )
        self.assertEqual([symbol["value"] for symbol in symbols], [None, None])
        self.assertEqual(result.errors.count(), 0)

    def test_input_undeclared_target_has_no_secondary_error(self):
        _, result = analyze_source("main { cin(missing); }")
        input_node = find_nodes(result.annotated_ast, "CIN")[0]

        self.assertEqual(input_node.get_annotation("semantic_status"), "error")
        self.assertEqual(
            [error.error_type for error in result.errors.get_objects()],
            ["undeclared_identifier"],
        )

    def test_output_analyzes_expression_without_changing_values(self):
        _, result = analyze_source(
            "main { int value = 4; cout(value + 2); }"
        )
        output = find_nodes(result.annotated_ast, "COUT")[0]
        expression = output.children[0]

        self.assertEqual(output.get_annotation("semantic_status"), "validated")
        self.assertEqual(expression.get_annotation("type"), "int")
        self.assertEqual(expression.get_annotation("value"), 6)
        self.assertEqual(result.symbol_table.get_all()[0]["value"], 4)
        self.assertEqual(result.errors.count(), 0)

    def test_shift_output_analyzes_all_expressions(self):
        _, result = analyze_source(
            "main { int value = 2; cout << value << value > 1 << value + 3; }"
        )
        output = find_nodes(result.annotated_ast, "COUT")[0]

        self.assertEqual(len(output.children), 3)
        self.assertEqual(
            [child.get_annotation("type") for child in output.children],
            ["int", "bool", "int"],
        )
        self.assertEqual(
            [child.get_annotation("value") for child in output.children],
            [2, True, 5],
        )
        self.assertEqual(result.symbol_table.get_all()[0]["value"], 2)
        self.assertEqual(result.errors.count(), 0)

    def test_output_analyzes_relational_and_logical_expression(self):
        _, result = analyze_source(
            "main { int value = 2; cout((value > 1) && (value < 3)); }"
        )
        output_expression = find_nodes(result.annotated_ast, "COUT")[0].children[0]

        self.assertEqual(output_expression.get_annotation("type"), "bool")
        self.assertEqual(output_expression.get_annotation("value"), True)
        self.assertEqual(result.symbol_table.get_all()[0]["value"], 2)
        self.assertEqual(result.errors.count(), 0)

    def test_output_propagates_expression_error(self):
        _, result = analyze_source("main { cout(missing + 1); }")
        output = find_nodes(result.annotated_ast, "COUT")[0]

        self.assertEqual(output.get_annotation("semantic_status"), "error")
        self.assertEqual(
            [error.error_type for error in result.errors.get_objects()],
            ["undeclared_identifier"],
        )

    def test_prefix_and_postfix_updates_preserve_form_and_value(self):
        _, result = analyze_source(
            "main { int value = 3; value++; --value; }"
        )
        updates = [
            node
            for node in find_nodes(result.annotated_ast, "OPERADOR")
            if node.get_token_type() in {TokenType.INCREMENT, TokenType.DECREMENT}
        ]

        self.assertEqual(
            [node.get_annotation("operator_form") for node in updates],
            ["postfix", "prefix"],
        )
        self.assertEqual([node.get_annotation("value") for node in updates], [3, 3])
        self.assertEqual(result.symbol_table.get_all()[0]["value"], 3)
        self.assertEqual(result.errors.count(), 0)

    def test_prefix_increment_can_supply_expression_value(self):
        _, result = analyze_source(
            "main { int value = 4; int derived = ++value + 2; }"
        )
        increment = find_operators(result.annotated_ast, TokenType.INCREMENT)[0]
        symbols = result.symbol_table.get_all()

        self.assertEqual(increment.get_annotation("type"), "int")
        self.assertEqual(increment.get_annotation("value"), 5)
        self.assertEqual([symbol["value"] for symbol in symbols], [5, 7])
        self.assertEqual(result.errors.count(), 0)

    def test_increment_of_unknown_value_remains_unknown(self):
        _, result = analyze_source("main { int value; value++; }")
        increment = find_operators(result.annotated_ast, TokenType.INCREMENT)[0]

        self.assertEqual(increment.get_annotation("semantic_status"), "validated")
        self.assertEqual(increment.get_annotation("type"), "int")
        self.assertIsNone(increment.get_annotation("value"))
        self.assertIsNone(result.symbol_table.get_all()[0]["value"])
        self.assertEqual(result.errors.count(), 0)

    def test_increment_requires_identifier_target(self):
        _, result = analyze_source('main { int value = ++"text"; }')
        increment = find_operators(result.annotated_ast, TokenType.INCREMENT)[0]

        self.assertEqual(increment.get_annotation("semantic_status"), "error")
        self.assertEqual(
            [error.error_type for error in result.errors.get_objects()],
            ["invalid_increment_target"],
        )

    def test_increment_rejects_incompatible_declared_type(self):
        analyzer = SemanticAnalyzer()
        symbol = analyzer.symbol_table.declare("text", "string", 1)
        symbol.value = "known"
        increment = SyntaxNode(
            "OPERADOR",
            Token(TokenType.INCREMENT, "++", 2, 5),
        )
        increment.add_child(
            SyntaxNode(
                "IDENTIFICADOR",
                Token(TokenType.IDENTIFIER, "text", 2, 7),
            )
        )

        inferred_type = analyzer.visit_update_expression(increment)

        self.assertIsNone(inferred_type)
        self.assertEqual(increment.get_annotation("semantic_status"), "error")
        self.assertEqual(symbol.value, "known")
        self.assertEqual(
            [error.error_type for error in analyzer.errors.get_objects()],
            ["invalid_operator"],
        )

    def test_increment_undeclared_identifier_has_no_secondary_error(self):
        _, result = analyze_source("main { missing++; }")

        self.assertEqual(
            [error.error_type for error in result.errors.get_objects()],
            ["undeclared_identifier"],
        )

    def test_equal_updates_in_if_branches_preserve_merged_value(self):
        _, result = analyze_source(
            "main { int value = 1; if (value > 0) { value++; } "
            "else { ++value; } }"
        )

        self.assertEqual(result.symbol_table.get_all()[0]["value"], 2)
        self.assertEqual(result.errors.count(), 0)

    def test_increment_in_loop_condition_is_flow_conservative(self):
        _, result = analyze_source(
            "main { int value = 0; while (++value < 3) { } "
            "int derived = value + 1; }"
        )
        increment = find_operators(result.annotated_ast, TokenType.INCREMENT)[0]
        symbols = result.symbol_table.get_all()

        self.assertEqual(increment.get_annotation("semantic_status"), "validated")
        self.assertEqual([symbol["value"] for symbol in symbols], [None, None])
        self.assertEqual(result.errors.count(), 0)

    def test_updates_in_post_test_loops_are_flow_conservative(self):
        _, result = analyze_source(
            "main { int first = 0; do { first++; } while (first < 2); "
            "int second = 0; do { ++second; } until (second == 2); }"
        )
        updates = [
            node
            for node in find_nodes(result.annotated_ast, "OPERADOR")
            if node.get_token_type() == TokenType.INCREMENT
        ]

        self.assertEqual(
            [node.get_annotation("semantic_status") for node in updates],
            ["validated", "validated"],
        )
        self.assertEqual(
            [symbol["value"] for symbol in result.symbol_table.get_all()],
            [None, None],
        )
        self.assertEqual(result.errors.count(), 0)

    def test_function_call_analyzes_arguments_not_callee_as_variable(self):
        _, result = analyze_source(
            "main { int value = 2; mystery(value, 1 + 2); }"
        )
        call = find_nodes(result.annotated_ast, "LLAMAR")[0]
        callee, identifier_argument, expression_argument = call.children
        error_types = [error.error_type for error in result.errors.get_objects()]

        self.assertEqual(callee.get_annotation("semantic_status"), "unsupported")
        self.assertEqual(identifier_argument.get_annotation("type"), "int")
        self.assertEqual(expression_argument.get_annotation("value"), 3)
        self.assertEqual(error_types, ["unsupported_node"])
        self.assertNotIn("undeclared_identifier", error_types)

    def test_function_call_invalidates_all_active_known_values(self):
        _, result = analyze_source(
            "main { int first = 1; int second = 2; mystery(); "
            "int derived = first + second; }"
        )
        symbols = result.symbol_table.get_all()

        self.assertEqual([symbol["value"] for symbol in symbols], [None, None, None])
        self.assertEqual(
            [error.error_type for error in result.errors.get_objects()],
            ["unsupported_node"],
        )

    def test_function_arguments_use_values_before_call_side_effects(self):
        _, result = analyze_source(
            "main { int value = 5; mystery(value + 1); }"
        )
        call = find_nodes(result.annotated_ast, "LLAMAR")[0]

        self.assertEqual(call.children[1].get_annotation("value"), 6)
        self.assertIsNone(result.symbol_table.get_all()[0]["value"])

    def test_function_call_argument_error_is_preserved(self):
        _, result = analyze_source("main { mystery(missing); }")
        call = find_nodes(result.annotated_ast, "LLAMAR")[0]

        self.assertEqual(call.get_annotation("semantic_status"), "error")
        self.assertEqual(
            [error.error_type for error in result.errors.get_objects()],
            ["undeclared_identifier", "unsupported_node"],
        )

    def test_function_call_in_expression_has_no_invented_return_type(self):
        _, result = analyze_source(
            "main { int source = 1; int target = mystery(source) + 1; }"
        )
        call = find_nodes(result.annotated_ast, "LLAMAR")[0]
        addition = find_operators(result.annotated_ast, TokenType.PLUS)[0]
        declaration_assignment = find_operators(
            result.annotated_ast, TokenType.ASSIGN
        )[1]

        self.assertIsNone(call.get_annotation("type"))
        self.assertEqual(addition.get_annotation("semantic_status"), "pending")
        self.assertEqual(
            declaration_assignment.get_annotation("semantic_status"),
            "pending",
        )
        self.assertEqual(
            [error.error_type for error in result.errors.get_objects()],
            ["unsupported_node"],
        )

    def test_output_call_keeps_explicit_unsupported_state_and_side_effects(self):
        _, result = analyze_source(
            "main { int value = 8; cout(mystery(value)); }"
        )
        output = find_nodes(result.annotated_ast, "COUT")[0]

        self.assertEqual(output.get_annotation("semantic_status"), "pending")
        self.assertIsNone(result.symbol_table.get_all()[0]["value"])
        self.assertEqual(
            [error.error_type for error in result.errors.get_objects()],
            ["unsupported_node"],
        )

    def test_logical_and_applies_rhs_effects_only_when_required(self):
        cases = [
            ("int gate = 0;", 0, 0, False),
            ("int gate = 1;", 1, 1, True),
            ("int gate;", None, None, None),
        ]

        for gate_declaration, expected_changed, expected_observed, expected_value in cases:
            with self.subTest(gate_declaration=gate_declaration):
                _, result = analyze_source(
                    "main { "
                    f"{gate_declaration} "
                    "int changed = 0; "
                    "cout((gate > 0) && (++changed > 0)); "
                    "int observed = changed; }"
                )
                symbols = {
                    symbol["name"]: symbol
                    for symbol in result.symbol_table.get_all()
                }
                logical = find_operators(result.annotated_ast, TokenType.AND)[0]

                self.assertEqual(symbols["changed"]["value"], expected_changed)
                self.assertEqual(symbols["observed"]["value"], expected_observed)
                self.assertEqual(logical.get_annotation("value"), expected_value)
                self.assertEqual(result.errors.count(), 0)

    def test_logical_or_applies_rhs_effects_only_when_required(self):
        cases = [
            ("int gate = 1;", 0, 0, True),
            ("int gate = 0;", 1, 1, True),
            ("int gate;", None, None, True),
        ]

        for gate_declaration, expected_changed, expected_observed, expected_value in cases:
            with self.subTest(gate_declaration=gate_declaration):
                _, result = analyze_source(
                    "main { "
                    f"{gate_declaration} "
                    "int changed = 0; "
                    "cout((gate > 0) || (++changed > 0)); "
                    "int observed = changed; }"
                )
                symbols = {
                    symbol["name"]: symbol
                    for symbol in result.symbol_table.get_all()
                }
                logical = find_operators(result.annotated_ast, TokenType.OR)[0]

                self.assertEqual(symbols["changed"]["value"], expected_changed)
                self.assertEqual(symbols["observed"]["value"], expected_observed)
                self.assertEqual(logical.get_annotation("value"), expected_value)
                self.assertEqual(result.errors.count(), 0)

    def test_short_circuit_handles_decrement_side_effects(self):
        _, skipped = analyze_source(
            "main { int gate = 0; int changed = 2; "
            "cout((gate > 0) && (--changed > 0)); int observed = changed; }"
        )
        _, executed = analyze_source(
            "main { int gate = 0; int changed = 2; "
            "cout((gate > 0) || (--changed > 0)); int observed = changed; }"
        )

        self.assertEqual(
            [symbol["value"] for symbol in skipped.symbol_table.get_all()],
            [0, 2, 2],
        )
        self.assertEqual(
            [symbol["value"] for symbol in executed.symbol_table.get_all()],
            [0, 1, 1],
        )
        self.assertEqual(skipped.errors.count(), 0)
        self.assertEqual(executed.errors.count(), 0)

    def test_short_circuit_controls_unknown_function_side_effects(self):
        _, skipped = analyze_source(
            "main { int gate = 0; int stable = 7; "
            "cout((gate > 0) && mystery(stable)); int observed = stable; }"
        )
        _, executed = analyze_source(
            "main { int gate = 1; int stable = 7; "
            "cout((gate > 0) && mystery(stable)); int observed = stable; }"
        )
        _, conditional = analyze_source(
            "main { int gate; int stable = 7; "
            "cout((gate > 0) && mystery(stable)); int observed = stable; }"
        )

        self.assertEqual(
            [symbol["value"] for symbol in skipped.symbol_table.get_all()],
            [0, 7, 7],
        )
        self.assertEqual(
            [symbol["value"] for symbol in executed.symbol_table.get_all()],
            [None, None, None],
        )
        self.assertEqual(
            [symbol["value"] for symbol in conditional.symbol_table.get_all()],
            [None, None, None],
        )
        self.assertEqual(
            [error.error_type for error in skipped.errors.get_objects()],
            ["unsupported_node"],
        )
        self.assertEqual(
            [error.error_type for error in executed.errors.get_objects()],
            ["unsupported_node"],
        )
        self.assertEqual(
            [error.error_type for error in conditional.errors.get_objects()],
            ["unsupported_node"],
        )

    def test_nested_logical_short_circuit_restores_all_rhs_effects(self):
        _, result = analyze_source(
            "main { int gate = 0; int first = 0; int second = 0; "
            "cout((gate > 0) && ((++first > 0) || (++second > 0))); }"
        )
        updates = find_operators(result.annotated_ast, TokenType.INCREMENT)

        self.assertEqual(
            [symbol["value"] for symbol in result.symbol_table.get_all()],
            [0, 0, 0],
        )
        self.assertEqual(len(updates), 2)
        self.assertTrue(
            all(
                update.get_annotation("semantic_status") == "validated"
                for update in updates
            )
        )
        self.assertEqual(result.errors.count(), 0)

    def test_short_circuit_side_effects_remain_correct_in_if_and_while(self):
        _, result = analyze_source(
            "main { int gate = 0; int changed = 0; "
            "if ((gate > 0) && (++changed > 0)) { } "
            "while ((gate > 0) && (++changed > 0)) { } "
            "int observed = changed; }"
        )

        self.assertEqual(
            [symbol["value"] for symbol in result.symbol_table.get_all()],
            [0, 0, 0],
        )
        self.assertEqual(result.errors.count(), 0)

    def test_valid_integer_and_real_powers_remain_constant(self):
        _, result = analyze_source(
            "main { int integer = 2 ^ 4; real square_root = 4.0 ^ 0.5; "
            "real negative_base = (-2.0) ^ 2.0; }"
        )
        powers = find_operators(result.annotated_ast, TokenType.POWER)

        self.assertEqual(
            [power.get_annotation("type") for power in powers],
            ["int", "real", "real"],
        )
        self.assertEqual(
            [power.get_annotation("value") for power in powers],
            [16, 2.0, 4.0],
        )
        self.assertEqual(result.errors.count(), 0)

    def test_power_outside_real_domain_is_rejected(self):
        _, result = analyze_source(
            "main {\n  real value = (-1.0) ^ 0.5;\n}"
        )
        power = find_operators(result.annotated_ast, TokenType.POWER)[0]
        error = result.errors.get_objects()[0]

        self.assertEqual(power.get_annotation("semantic_status"), "error")
        self.assertIsNone(power.get_annotation("value"))
        self.assertIsNone(result.symbol_table.get_all()[0]["value"])
        self.assertEqual(error.error_type, "constant_evaluation_error")
        self.assertEqual((error.line, error.column), (2, 23))

    def test_multiline_prefix_and_postfix_updates_preserve_form(self):
        _, result = analyze_source(
            "main {\n"
            "  int post_inc = 1;\n"
            "  post_inc\n"
            "  ++;\n"
            "  int post_dec = 3;\n"
            "  post_dec\n"
            "  --;\n"
            "  int pre_inc = 1;\n"
            "  ++\n"
            "  pre_inc;\n"
            "  int pre_dec = 3;\n"
            "  --\n"
            "  pre_dec;\n"
            "}"
        )
        updates = [
            node
            for node in find_nodes(result.annotated_ast, "OPERADOR")
            if node.get_token_type() in {TokenType.INCREMENT, TokenType.DECREMENT}
        ]

        self.assertEqual(
            [update.get_annotation("operator_form") for update in updates],
            ["postfix", "postfix", "prefix", "prefix"],
        )
        self.assertEqual(
            [update.get_annotation("value") for update in updates],
            [1, 3, 2, 2],
        )
        self.assertEqual(
            [symbol["value"] for symbol in result.symbol_table.get_all()],
            [2, 2, 2, 2],
        )
        self.assertEqual(result.errors.count(), 0)

    def test_semantic_diagnostics_preserve_source_locations(self):
        cases = [
            (
                "undeclared_identifier",
                "main {\n  missing = 1;\n}",
                (2, 3),
            ),
            (
                "duplicate_identifier",
                "main {\n  int value;\n  int value;\n}",
                (3, 7),
            ),
            (
                "invalid_conversion",
                "main {\n  int value = 1.5;\n}",
                (2, 13),
            ),
            (
                "invalid_operator",
                'main {\n  int value = "text" + 1;\n}',
                (2, 22),
            ),
            (
                "invalid_condition",
                "main {\n  if (1) { int value; }\n}",
                (2, 7),
            ),
            (
                "division_by_zero",
                "main {\n  real value = 1 / 0;\n}",
                (2, 18),
            ),
            (
                "unsupported_node",
                "main {\n  mystery();\n}",
                (2, 3),
            ),
        ]

        for error_type, source, expected_location in cases:
            with self.subTest(error_type=error_type):
                _, result = analyze_source(source)
                errors = result.errors.get_objects()

                self.assertEqual(len(errors), 1)
                self.assertEqual(errors[0].error_type, error_type)
                self.assertEqual(
                    (errors[0].line, errors[0].column),
                    expected_location,
                )

    def test_regression_fixes_preserve_original_ast(self):
        source = (
            "main { int gate = 0; int value = 1; "
            "cout((gate > 0) && (++value > 0)); value\n++; "
            "real invalid = (-1.0) ^ 0.5; }"
        )
        tokens, lexical_errors = Lexer(source).tokenize()
        self.assertEqual(lexical_errors, [])
        ast = Parser(tokens).parse()
        original = ast.to_semantic_dict()

        SemanticAnalyzer().analyze(ast)

        self.assertEqual(ast.to_semantic_dict(), original)

    def test_regression_fix_analyses_do_not_share_state(self):
        analyzer = SemanticAnalyzer()
        first_tokens, first_errors = Lexer(
            "main { int gate = 0; int changed = 0; "
            "cout((gate > 0) && (++changed > 0)); }"
        ).tokenize()
        second_tokens, second_errors = Lexer(
            "main { int changed = 4; ++changed; }"
        ).tokenize()
        self.assertEqual(first_errors, [])
        self.assertEqual(second_errors, [])

        first = analyzer.analyze(Parser(first_tokens).parse())
        second = analyzer.analyze(Parser(second_tokens).parse())

        self.assertEqual(first.symbol_table.get_all()[1]["value"], 0)
        self.assertEqual(second.symbol_table.get_all()[0]["value"], 5)
        self.assertIsNot(first.symbol_table, second.symbol_table)
        self.assertIsNot(first.errors, second.errors)

    def test_input_output_update_and_call_work_in_one_program(self):
        _, result = analyze_source(
            "main { int input = 1; int counter = 2; cin(input); ++counter; "
            "cout << input << counter + 1; mystery(input, counter); }"
        )
        input_node = find_nodes(result.annotated_ast, "CIN")[0]
        output_node = find_nodes(result.annotated_ast, "COUT")[0]
        update = find_operators(result.annotated_ast, TokenType.INCREMENT)[0]
        call = find_nodes(result.annotated_ast, "LLAMAR")[0]

        self.assertEqual(input_node.get_annotation("semantic_status"), "validated")
        self.assertEqual(output_node.get_annotation("semantic_status"), "validated")
        self.assertEqual(update.get_annotation("value"), 3)
        self.assertEqual(call.get_annotation("semantic_status"), "unsupported")
        self.assertEqual(
            [symbol["value"] for symbol in result.symbol_table.get_all()],
            [None, None],
        )
        self.assertEqual(
            [error.error_type for error in result.errors.get_objects()],
            ["unsupported_node"],
        )

    def test_block_five_constructs_preserve_original_ast(self):
        source = (
            "main { int value = 1; cin(value); ++value; cout(value); "
            "mystery(value); }"
        )
        tokens, lexical_errors = Lexer(source).tokenize()
        self.assertEqual(lexical_errors, [])
        ast = Parser(tokens).parse()
        original = ast.to_semantic_dict()

        SemanticAnalyzer().analyze(ast)

        self.assertEqual(ast.to_semantic_dict(), original)

    def test_original_ast_is_not_modified(self):
        ast = make_structural_ast()
        original = ast.to_semantic_dict()

        SemanticAnalyzer().analyze(ast)

        self.assertEqual(ast.to_semantic_dict(), original)

    def test_annotated_ast_is_an_independent_copy(self):
        ast = make_structural_ast()
        result = SemanticAnalyzer().analyze(ast)

        self.assertIsNot(result.annotated_ast, ast)
        self.assertIsNot(result.annotated_ast.children[0], ast.children[0])

        result.annotated_ast.children[0].name = "CHANGED"
        self.assertEqual(ast.children[0].name, "MAIN")

    def test_structural_nodes_are_visited_with_scopes(self):
        result = SemanticAnalyzer().analyze(make_structural_ast())
        program = result.annotated_ast
        main = program.children[0]
        block = main.children[0]
        nested_block = block.children[0]

        self.assertEqual(program.get_annotation("semantic_status"), "structural")
        self.assertEqual(main.get_annotation("semantic_status"), "structural")
        self.assertEqual(block.get_annotation("semantic_status"), "structural")
        self.assertEqual(nested_block.get_annotation("semantic_status"), "structural")
        self.assertEqual(program.get_annotation("scope"), "global")
        self.assertEqual(main.get_annotation("scope"), "global")
        self.assertEqual(block.get_annotation("scope"), "scope_1")
        self.assertEqual(nested_block.get_annotation("scope"), "scope_2")
        self.assertEqual(result.errors.count(), 0)

    def test_consecutive_analyses_do_not_share_state(self):
        analyzer = SemanticAnalyzer()
        first = analyzer.analyze(make_structural_ast())
        first.symbol_table.declare("first_only", "int")
        first.errors.add_error("test", "first only")

        second = analyzer.analyze(make_structural_ast())

        self.assertIsNot(first.symbol_table, second.symbol_table)
        self.assertIsNot(first.errors, second.errors)
        self.assertFalse(second.symbol_table.exists("first_only"))
        self.assertEqual(second.errors.count(), 0)

    def test_invalid_inputs_are_rejected(self):
        analyzer = SemanticAnalyzer()

        with self.assertRaises(ValueError):
            analyzer.analyze(None)

        with self.assertRaises(TypeError):
            analyzer.analyze(object())

        with self.assertRaises(ValueError):
            analyzer.analyze(SyntaxNode("MAIN"))

        invalid_child = SyntaxNode("PROGRAMA")
        invalid_child.children.append("not a node")
        with self.assertRaises(TypeError):
            analyzer.analyze(invalid_child)

    def test_unsupported_nodes_are_reported_and_traversed(self):
        ast = make_structural_ast()
        unsupported = SyntaxNode("FUTURE_NODE")
        nested_block = SyntaxNode("BLOQUE")
        unsupported.add_child(nested_block)
        ast.children[0].children[0].add_child(unsupported)

        result = SemanticAnalyzer().analyze(ast)
        annotated_unsupported = (
            result.annotated_ast.children[0].children[0].children[1]
        )

        self.assertEqual(
            annotated_unsupported.get_annotation("semantic_status"),
            "unsupported",
        )
        self.assertEqual(result.errors.count(), 1)
        self.assertEqual(
            result.errors.get_objects()[0].error_type,
            "unsupported_node",
        )
        self.assertEqual(
            annotated_unsupported.children[0].get_annotation("semantic_status"),
            "structural",
        )


if __name__ == "__main__":
    unittest.main()
