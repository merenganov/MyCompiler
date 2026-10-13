import unittest

from ui.ide_window import IDEWindow


class FakeTextArea:
    def __init__(self, source):
        self.source = source

    def get(self, start, end):
        return self.source


class FakeNotebook:
    def __init__(self):
        self.selections = []

    def select(self, index):
        self.selections.append(index)


class FakePanels:
    def __init__(self):
        self.lexico = "lexico"
        self.sintactico = "sintactico"
        self.semantico = "semantico"
        self.simbolos = "simbolos"
        self.err_lex = "err_lex"
        self.err_sin = "err_sin"
        self.err_sem = "err_sem"
        self.results_notebook = FakeNotebook()
        self.bottom_pane = FakeNotebook()
        self.output = {}

    def set_text(self, widget, content):
        self.output[widget] = content


def make_headless_window(source):
    window = IDEWindow.__new__(IDEWindow)
    window.text_area = FakeTextArea(source)
    window.panels = FakePanels()
    window.opened_semantic_trees = []
    window._open_semantic_tree_window = window.opened_semantic_trees.append
    return window


class SemanticIDEIntegrationTests(unittest.TestCase):
    def test_valid_program_displays_real_semantic_results(self):
        window = make_headless_window(
            "main { int count = 1; real total = count + 2.5; cout(total); }"
        )

        window._ui_compile_sem()

        semantic_output = window.panels.output[window.panels.semantico]
        syntax_output = window.panels.output[window.panels.sintactico]
        symbol_output = window.panels.output[window.panels.simbolos]

        self.assertIn("Análisis semántico correcto", semantic_output)
        self.assertIn("PROGRAMA", semantic_output)
        self.assertIn("Análisis sintáctico correcto", syntax_output)
        self.assertIn("PROGRAMA", syntax_output)
        self.assertIn("count", symbol_output)
        self.assertIn("total", symbol_output)
        self.assertEqual(
            window.panels.output[window.panels.err_sem],
            "Sin errores semánticos.\n",
        )
        self.assertEqual(len(window.opened_semantic_trees), 1)

    def test_semantic_diagnostics_are_displayed_by_the_real_analyzer(self):
        cases = [
            ("main { missing = 1; }", "undeclared_identifier"),
            ("main { int value; real value; }", "duplicate_identifier"),
            ('main { int value = "text"; }', "type_mismatch"),
            ("main { int value = 1.5; }", "invalid_conversion"),
            ('main { int value = "text" + 1; }', "invalid_operator"),
            ("main { if (1) { int value; } }", "invalid_condition"),
            ("main { mystery(); }", "unsupported_node"),
        ]

        for source, error_type in cases:
            with self.subTest(error_type=error_type):
                window = make_headless_window(source)
                window._ui_compile_sem()

                semantic_output = window.panels.output[window.panels.semantico]
                error_output = window.panels.output[window.panels.err_sem]

                self.assertIn("completado con 1 error", semantic_output)
                self.assertIn(f"[{error_type}]", error_output)
                self.assertEqual(len(window.opened_semantic_trees), 1)

    def test_valid_conversion_and_constant_value_reach_the_views(self):
        window = make_headless_window(
            "main { real converted = 1; int constant = 2 + 3 * 4; }"
        )

        window._ui_compile_sem()

        semantic_output = window.panels.output[window.panels.semantico]
        symbol_output = window.panels.output[window.panels.simbolos]

        self.assertIn("int -> real", semantic_output)
        self.assertIn("converted", symbol_output)
        self.assertIn("constant", symbol_output)
        self.assertIn("14", symbol_output)
        self.assertEqual(
            window.panels.output[window.panels.err_sem],
            "Sin errores semánticos.\n",
        )

    def test_multiple_semantic_errors_are_preserved(self):
        window = make_headless_window(
            "main { int value; real value; missing = 1; if (1) { } }"
        )

        window._ui_compile_sem()

        error_output = window.panels.output[window.panels.err_sem]

        self.assertIn("[duplicate_identifier]", error_output)
        self.assertIn("[undeclared_identifier]", error_output)
        self.assertIn("[invalid_condition]", error_output)
        self.assertIn(
            "completado con 3 error",
            window.panels.output[window.panels.semantico],
        )

    def test_lexical_and_syntax_errors_stop_later_phases(self):
        cases = [
            (
                "main { int value = 1; @ }",
                "errores léxicos",
                "err_lex",
            ),
            (
                "main { int value = 1 }",
                "errores sintácticos",
                "err_sin",
            ),
        ]

        for source, expected_message, error_panel in cases:
            with self.subTest(expected_message=expected_message):
                window = make_headless_window(source)
                window._ui_compile_sem()

                self.assertIn(
                    expected_message,
                    window.panels.output[window.panels.semantico],
                )
                self.assertTrue(window.panels.output[getattr(window.panels, error_panel)])
                self.assertIn(
                    "Sin símbolos registrados",
                    window.panels.output[window.panels.simbolos],
                )
                self.assertEqual(window.opened_semantic_trees, [])

    def test_consecutive_analyses_clear_previous_results(self):
        window = make_headless_window("main { int first; missing = 1; }")
        window._ui_compile_sem()

        window.text_area.source = "main { int second = 2; }"
        window._ui_compile_sem()

        symbol_output = window.panels.output[window.panels.simbolos]

        self.assertNotIn("first", symbol_output)
        self.assertNotIn("missing", symbol_output)
        self.assertIn("second", symbol_output)
        self.assertEqual(
            window.panels.output[window.panels.err_sem],
            "Sin errores semánticos.\n",
        )
        self.assertEqual(len(window.opened_semantic_trees), 2)


if __name__ == "__main__":
    unittest.main()
