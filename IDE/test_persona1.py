from core.symbol_table import SymbolTable
from core.semantic_errors import SemanticErrorManager


def print_separator(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


# ==========================================================
# CREACIÓN DE OBJETOS
# ==========================================================

table = SymbolTable()
errors = SemanticErrorManager()


# ==========================================================
# PRUEBA 1 - DECLARACIONES
# ==========================================================

print_separator("PRUEBA 1 - DECLARACIONES")

table.declare("x", "int", line=4)
table.declare("y", "int", line=4)
table.declare("z", "int", line=4)

table.declare("a", "real", line=5)
table.declare("b", "real", line=5)
table.declare("c", "real", line=5)

for symbol in table.get_all():
    print(symbol)


# ==========================================================
# PRUEBA 2 - BÚSQUEDA
# ==========================================================

print_separator("PRUEBA 2 - BÚSQUEDA")

print("Existe x:", table.exists("x"))
print("Existe a:", table.exists("a"))
print("Existe suma:", table.exists("suma"))

print("Tipo de x:", table.get_type("x"))
print("Tipo de a:", table.get_type("a"))


# ==========================================================
# PRUEBA 3 - REGISTRO DE USOS
# ==========================================================

print_separator("PRUEBA 3 - REGISTRO DE USOS")

table.add_usage("x", 7)
table.add_usage("x", 8)
table.add_usage("x", 13)

table.add_usage("y", 9)
table.add_usage("y", 10)
table.add_usage("y", 11)

table.add_usage("a", 12)
table.add_usage("a", 18)

for symbol in table.get_all():
    print(symbol)


# ==========================================================
# PRUEBA 4 - IDENTIFICADOR NO DECLARADO
# ==========================================================

print_separator("PRUEBA 4 - IDENTIFICADOR NO DECLARADO")

if not table.exists("suma"):
    errors.undeclared_identifier(
        name="suma",
        line=6,
        column=1
    )

if not table.exists("mas"):
    errors.undeclared_identifier(
        name="mas",
        line=36,
        column=4
    )


# ==========================================================
# PRUEBA 5 - DECLARACIÓN DUPLICADA
# ==========================================================

print_separator("PRUEBA 5 - DECLARACIÓN DUPLICADA")

if table.exists("x", current_scope_only=True):
    errors.duplicate_identifier(
        name="x",
        scope=table.current_scope(),
        line=20,
        column=1
    )


# ==========================================================
# PRUEBA 6 - ÁMBITOS
# ==========================================================

print_separator("PRUEBA 6 - ÁMBITOS")

print("Ámbito actual:", table.current_scope())

table.enter_scope("if_1")

print("Nuevo ámbito:", table.current_scope())

table.declare("temporal", "int", line=20)

print("Existe temporal:", table.exists("temporal"))
print("Existe x desde ámbito interno:", table.exists("x"))

for symbol in table.get_all():
    print(symbol)

table.exit_scope()

print("Ámbito después de salir:", table.current_scope())


# ==========================================================
# PRUEBA 7 - ERRORES DE TIPOS
# ==========================================================

print_separator("PRUEBA 7 - ERRORES DE TIPOS")

errors.type_mismatch(
    expected_type="int",
    received_type="real",
    line=7,
    column=3
)

errors.invalid_conversion(
    source_type="real",
    target_type="int",
    line=7,
    column=3
)

errors.invalid_operator(
    operator="+",
    left_type="bool",
    right_type="int",
    line=25,
    column=5
)

errors.invalid_condition(
    received_type="int",
    line=30,
    column=1
)


# ==========================================================
# RESULTADO FINAL
# ==========================================================

print_separator("TABLA FINAL")

for symbol in table.get_all():
    print(symbol)


print_separator("ERRORES SEMÁNTICOS")

for error in errors.get_objects():
    print(error)


print_separator("RESUMEN")

print("Cantidad de símbolos:", len(table.get_all()))
print("Cantidad de errores:", errors.count())
print("¿Hay errores?:", errors.has_errors())