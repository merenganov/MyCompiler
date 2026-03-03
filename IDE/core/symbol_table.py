class SymbolTable:
    def __init__(self):
        self.symbols = {}

    def declare(self, name, type_):
        if name in self.symbols:
            raise Exception(f"Variable '{name}' ya declarada")
        self.symbols[name] = {
            "type": type_,
            "value": None
        }

    def assign(self, name, value):
        if name not in self.symbols:
            raise Exception(f"Variable '{name}' no declarada")
        self.symbols[name]["value"] = value

    def get_all(self):
        return self.symbols