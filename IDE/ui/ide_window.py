import os



import tkinter as tk



from tkinter import ttk, font







from core.state import IDEState



from core.file_manager import FileManager



from core.lexer import Lexer



from core.parser import Parser



from core.syntax_error import SyntaxErrorCompiler



from core.semantic import SemanticAnalyzer







from ui.menu import IDEMenu



from ui.toolbar import Toolbar



from ui.panels import Panels











class IDEWindow:



    THEMES = {



        "dark": {



            "text_bg": "#1e1e1e",



            "text_fg": "#d4d4d4",



            "panel_bg": "#252526",



            "line_fg": "#858585",



            "select_bg": "#264f78",



            "cursor": "#ffffff",



            "syntax": {



                "KEYWORD": "#569CD6",



                "IDENTIFIER": "#D4D4D4",



                "NUMBER": "#B5CEA8",



                "STRING": "#CE9178",



                "OPERATOR": "#C586C0",



                "SYMBOL": "#DCDCAA",



                "COMMENT": "#6A9955",



                "ERROR": "#F44747",



            }



        },



        "light": {



            "text_bg": "#ffffff",



            "text_fg": "#111111",



            "panel_bg": "#e6e6e6",



            "line_fg": "#666666",



            "select_bg": "#cce6ff",



            "cursor": "#000000",



            "syntax": {



                "KEYWORD": "#0000CC",



                "IDENTIFIER": "#111111",



                "NUMBER": "#098658",



                "STRING": "#A31515",



                "OPERATOR": "#AF00DB",



                "SYMBOL": "#795E26",



                "COMMENT": "#008000",



                "ERROR": "#CC0000",



            }



        }



    }







    def __init__(self, root: tk.Tk, apply_theme_callback, default_theme: str = "dark"):



        self.root = root



        self.root.title("IDE")



        self.root.geometry("1100x700")







        self.apply_theme_callback = apply_theme_callback



        self.theme_mode = default_theme







        self.state = IDEState()



        actions = {}







        self.top_container = ttk.Frame(self.root)



        self.top_container.pack(side=tk.TOP, fill=tk.X)







        self.bottom_container = ttk.Frame(self.root)



        self.bottom_container.pack(side=tk.BOTTOM, fill=tk.X)







        self.center_container = ttk.Frame(self.root)



        self.center_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)







        self.status = ttk.Label(self.bottom_container, text="Ln 1, Col 1", anchor="e")



        self.status.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=8)







        self.panels = Panels(self.center_container)







        self._build_editor(self.panels.editor_container)



        self._configure_syntax_tags()







        self.file_manager = FileManager(



            state=self.state,



            editor_text_widget=self.text_area,



            root=self.root,



            on_after_change=self._after_file_change



        )







        if hasattr(self.panels, "project_tree"):



            self.panels.project_tree.bind("<Double-1>", self._on_tree_open)







        actions.update({



            "new": self.file_manager.new_file,



            "open": self.file_manager.open_file,



            "open_project": (lambda: self.file_manager.open_project_folder(self.panels.project_tree))



            if hasattr(self.panels, "project_tree") else (lambda: None),



            "close": self.file_manager.close_file,



            "save": self.file_manager.save,



            "save_as": self.file_manager.save_as,



            "exit": self.file_manager.exit_app,







            "compile_lex": self._ui_compile_lex,



            "compile_syn": self._ui_compile_syn,



            "compile_sem": self._ui_compile_sem,



            "compile_ir": self._ui_compile_ir,







            "run": self._ui_run,



            "pause": self._ui_pause,



            "stop": self._ui_stop,







            "toggle_theme": self.toggle_theme,



        })







        self.root.config(menu=IDEMenu(self.root, actions).build())







        self.toolbar = Toolbar(self.top_container, actions)



        self.toolbar.pack(side=tk.TOP, fill=tk.X)







        self.apply_theme_to_widgets()



        self._update_title()







        self.root.after(50, self._update_cursor_status)



        self.root.after(100, self._apply_syntax_highlighting)







    # ====================================================



    # THEME



    # ====================================================







    def toggle_theme(self):



        self.theme_mode = "light" if self.theme_mode == "dark" else "dark"



        self.apply_theme_callback(self.theme_mode)



        self.apply_theme_to_widgets()



        self._configure_syntax_tags()



        self._redraw_line_numbers()



        self._update_cursor_status()



        self._apply_syntax_highlighting()







    def apply_theme_to_widgets(self):



        t = self.THEMES[self.theme_mode]







        self.text_area.configure(



            bg=t["text_bg"],



            fg=t["text_fg"],



            insertbackground=t["cursor"],



            selectbackground=t["select_bg"],



        )







        self.line_numbers.configure(background=t["panel_bg"])







        if hasattr(self.panels, "apply_text_theme"):



            self.panels.apply_text_theme(



                bg=t["text_bg"],



                fg=t["text_fg"],



                cursor=t["cursor"],



                select_bg=t["select_bg"]



            )







    # ====================================================



    # EDITOR



    # ====================================================







    def _build_editor(self, parent):



        frame = ttk.Frame(parent)



        frame.pack(fill=tk.BOTH, expand=True)







        self.line_numbers = tk.Canvas(frame, width=50, highlightthickness=0)



        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)







        self.editor_scrollbar = ttk.Scrollbar(frame)



        self.editor_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)







        self.text_area = tk.Text(



            frame,



            wrap="none",



            undo=True,



            yscrollcommand=self._on_textscroll,



            relief="flat",



            borderwidth=0



        )







        try:



            self.text_area.configure(font=("Consolas", 11))



        except Exception:



            pass







        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)



        self.editor_scrollbar.config(command=self._on_scroll)







        self.text_area.bind("<<Modified>>", self._on_modified)



        self.text_area.bind("<KeyRelease>", self._on_cursor_move)



        self.text_area.bind("<KeyPress>", self._on_cursor_move)



        self.text_area.bind("<Button-1>", self._on_cursor_move)



        self.text_area.bind("<ButtonRelease-1>", self._on_cursor_move)



        self.text_area.bind("<MouseWheel>", self._on_mousewheel)



        self.text_area.bind("<Button-4>", self._on_mousewheel)



        self.text_area.bind("<Button-5>", self._on_mousewheel)



        self.text_area.bind("<Configure>", lambda e: self._redraw_line_numbers())







        self._redraw_line_numbers()



        self._update_cursor_status()







    def _configure_syntax_tags(self):



        syntax = self.THEMES[self.theme_mode]["syntax"]







        self.text_area.tag_config("KEYWORD", foreground=syntax["KEYWORD"])



        self.text_area.tag_config("IDENTIFIER", foreground=syntax["IDENTIFIER"])



        self.text_area.tag_config("NUMBER", foreground=syntax["NUMBER"])



        self.text_area.tag_config("STRING", foreground=syntax["STRING"])



        self.text_area.tag_config("OPERATOR", foreground=syntax["OPERATOR"])



        self.text_area.tag_config("SYMBOL", foreground=syntax["SYMBOL"])



        self.text_area.tag_config("COMMENT", foreground=syntax["COMMENT"])



        self.text_area.tag_config("ERROR", foreground=syntax["ERROR"], underline=True)







    def _clear_syntax_tags(self):



        for tag in ["KEYWORD", "IDENTIFIER", "NUMBER", "STRING", "OPERATOR", "SYMBOL", "COMMENT", "ERROR"]:



            self.text_area.tag_remove(tag, "1.0", "end")







    def _token_tag_name(self, token_type_name: str) -> str:



        keywords = {



            "INT", "FLOAT", "REAL_TYPE", "IF", "ELSE", "THEN", "END",



            "DO", "WHILE", "UNTIL", "CIN", "COUT", "MAIN"



        }



        numbers = {"INTEGER", "REAL"}



        strings = {"STRING", "CHAR"}



        operators = {



            "PLUS", "MINUS", "STAR", "SLASH", "MODULO", "POWER",



            "INCREMENT", "DECREMENT",



            "ASSIGN", "EQUAL", "NOT_EQUAL", "LESS", "LESS_EQUAL",



            "GREATER", "GREATER_EQUAL", "AND", "OR", "NOT"



        }



        symbols = {



            "LPAREN", "RPAREN", "LBRACE", "RBRACE",



            "LBRACKET", "RBRACKET", "SEMICOLON", "COMMA", "DOT"



        }







        if token_type_name in keywords:



            return "KEYWORD"



        if token_type_name == "IDENTIFIER":



            return "IDENTIFIER"



        if token_type_name in numbers:



            return "NUMBER"



        if token_type_name in strings:



            return "STRING"



        if token_type_name in operators:



            return "OPERATOR"



        if token_type_name in symbols:



            return "SYMBOL"







        return "IDENTIFIER"







    def _apply_syntax_highlighting(self):



        code = self.text_area.get("1.0", "end-1c")



        self._clear_syntax_tags()







        try:



            result = Lexer(code).tokenize()



        except Exception:



            return







        if isinstance(result, tuple) and len(result) == 2:



            tokens, errors = result



        else:



            tokens = result



            errors = []







        for token in tokens:



            token_type = getattr(token, "token_type", getattr(token, "type", None))



            if token_type is None:



                continue







            token_type_name = token_type.name if hasattr(token_type, "name") else str(token_type)







            if token_type_name == "EOF":



                continue







            lexeme = getattr(token, "lexeme", "")



            line = getattr(token, "line", None)



            column = getattr(token, "column", None)







            if line is None or column is None or lexeme == "":



                continue







            start_index = f"{line}.{column - 1}"



            end_index = f"{line}.{column - 1 + len(lexeme)}"



            tag_name = self._token_tag_name(token_type_name)







            self.text_area.tag_add(tag_name, start_index, end_index)







        for error in errors:



            line = getattr(error, "line", None)



            column = getattr(error, "column", None)



            char = getattr(error, "character", "")







            if line is None or column is None:



                continue







            length = max(1, len(str(char))) if char else 1



            start_index = f"{line}.{column - 1}"



            end_index = f"{line}.{column - 1 + length}"







            self.text_area.tag_add("ERROR", start_index, end_index)







    def _on_textscroll(self, first, last):



        self.editor_scrollbar.set(first, last)



        self._redraw_line_numbers()



        self._update_cursor_status()







    def _on_scroll(self, *args):



        self.text_area.yview(*args)



        self._redraw_line_numbers()



        self._update_cursor_status()







    def _on_mousewheel(self, event):



        self.root.after_idle(self._redraw_line_numbers)



        self.root.after_idle(self._update_cursor_status)







    def _on_modified(self, event=None):



        if self.text_area.edit_modified():



            self.state.is_dirty = True



            self.text_area.edit_modified(False)



            self._update_title()



            self._redraw_line_numbers()



            self._update_cursor_status()



            self._apply_syntax_highlighting()







    def _on_cursor_move(self, event=None):



        self._update_cursor_status()



        self._redraw_line_numbers()







    def _update_cursor_status(self):



        try:



            pos = self.text_area.index(tk.INSERT)



            line, col = pos.split(".")



            self.status.config(text=f"Ln {line}, Col {int(col) + 1}")



        except Exception:



            self.status.config(text="Ln 1, Col 1")







    def _redraw_line_numbers(self):



        self.line_numbers.delete("all")







        t = self.THEMES[self.theme_mode]



        line_color = t["line_fg"]







        f = font.Font(font=self.text_area["font"])



        _ = f.metrics("linespace")







        first = int(self.text_area.index("@0,0").split(".")[0])



        last = int(self.text_area.index(f"@0,{self.text_area.winfo_height()}").split(".")[0])







        for line in range(first, last + 1):



            dline = self.text_area.dlineinfo(f"{line}.0")



            if dline:



                y = dline[1]



                self.line_numbers.create_text(46, y, anchor="ne", text=str(line), fill=line_color)







    # ====================================================



    # FILE CALLBACKS



    # ====================================================







    def _refresh_project_explorer_if_needed(self):



        if not hasattr(self.panels, "project_tree"):



            return



        if not getattr(self.file_manager, "project_root", None):



            return



        if not hasattr(self.file_manager, "refresh_project_tree"):



            return







        try:



            self.file_manager.refresh_project_tree(self.panels.project_tree)



        except Exception:



            pass







    def _after_file_change(self, status: str):



        self._update_title()



        self._redraw_line_numbers()



        self._update_cursor_status()



        self._refresh_project_explorer_if_needed()



        self._apply_syntax_highlighting()







    def _update_title(self):



        name = self.state.current_file if self.state.current_file else "Nuevo Archivo"



        star = "*" if self.state.is_dirty else ""



        self.root.title(f"IDE - {name}{star}")







    # ====================================================



    # EXPLORADOR EVENTS



    # ====================================================







    def _on_tree_open(self, event=None):



        item = self.panels.project_tree.focus()



        if not item:



            return







        values = self.panels.project_tree.item(item, "values")



        if not values:



            return







        path = values[0]



        if path and os.path.isfile(path):



            self.file_manager.open_file_path(path)







    # ====================================================



    # HELPERS PARA ERRORES Y ÁRBOL



    # ====================================================







    def _set_syntax_error_output(self, text: str):



        possible_names = [



            "err_syn",



            "err_sin",



            "err_sintactico",



            "err_sintacticos",



            "errores_sintacticos",



        ]







        for name in possible_names:



            if hasattr(self.panels, name):



                try:



                    self.panels.bottom_pane.select(1)



                except Exception:



                    pass







                self.panels.set_text(getattr(self.panels, name), text)



                return







        self.panels.set_text(self.panels.sintactico, text)







    def _set_lexical_error_output(self, text: str):



        if hasattr(self.panels, "err_lex"):



            try:



                self.panels.bottom_pane.select(0)



            except Exception:



                pass







            self.panels.set_text(self.panels.err_lex, text)







    def _set_semantic_error_output(self, text: str):

        """

        Muestra los errores semánticos en el panel correspondiente.

        Si todavía no existe una pestaña específica, usa el panel semántico.

        """

        possible_names = [

            "err_sem",

            "err_semantico",

            "err_semanticos",

            "errores_semanticos",

        ]



        for name in possible_names:

            if hasattr(self.panels, name):

                try:

                    self.panels.bottom_pane.select(2)

                except Exception:

                    pass



                self.panels.set_text(getattr(self.panels, name), text)

                return



        if hasattr(self.panels, "semantico"):

            self.panels.set_text(self.panels.semantico, text)





    def _set_symbol_table_output(self, symbols):
        """
        Muestra la tabla de símbolos de forma ordenada y legible.

        Conserva la misma información de la Fase 3, pero separa
        visualmente las columnas para evitar que, por ejemplo, una
        línea 38 y una dirección 0 se vean como "380".
        """
        lines = []

        header = (
            f"{'NOMBRE':<12} | "
            f"{'TIPO':<10} | "
            f"{'LINEAS':<45} | "
            f"{'DIRECCION':<10} | "
            f"{'AMBITO':<15} | "
            f"{'VALOR':<15}"
        )

        lines.append(header)
        lines.append("-" * len(header))

        if not symbols:
            lines.append("Sin símbolos registrados.")
        else:
            for symbol in symbols:
                name = symbol.get("name", "")
                data_type = symbol.get("data_type", "")
                symbol_lines = symbol.get("lines", [])

                if isinstance(symbol_lines, list):
                    symbol_lines = ", ".join(str(line) for line in symbol_lines)

                if not symbol_lines:
                    symbol_lines = "-"

                address = symbol.get("address", None)
                scope = symbol.get("scope", None)
                value = symbol.get("value", None)

                address_text = str(address) if address is not None else "-"
                scope_text = str(scope) if scope is not None else "-"
                value_text = str(value) if value is not None else "-"

                lines.append(
                    f"{str(name):<12} | "
                    f"{str(data_type):<10} | "
                    f"{str(symbol_lines):<45} | "
                    f"{address_text:<10} | "
                    f"{scope_text:<15} | "
                    f"{value_text:<15}"
                )

        text = "\n".join(lines) + "\n"

        if hasattr(self.panels, "simbolos"):
            self.panels.set_text(self.panels.simbolos, text)


    def _open_syntax_tree_window(self, syntax_tree):



        window = tk.Toplevel(self.root)



        window.title("Árbol Sintáctico")



        window.geometry("900x600")







        container = ttk.Frame(window)



        container.pack(fill=tk.BOTH, expand=True)







        tree = ttk.Treeview(container)



        tree.heading("#0", text="Árbol Sintáctico", anchor="w")







        y_scroll = ttk.Scrollbar(container, orient=tk.VERTICAL, command=tree.yview)



        x_scroll = ttk.Scrollbar(container, orient=tk.HORIZONTAL, command=tree.xview)







        tree.configure(



            yscrollcommand=y_scroll.set,



            xscrollcommand=x_scroll.set



        )







        tree.grid(row=0, column=0, sticky="nsew")



        y_scroll.grid(row=0, column=1, sticky="ns")



        x_scroll.grid(row=1, column=0, sticky="ew")







        container.rowconfigure(0, weight=1)



        container.columnconfigure(0, weight=1)







        self._insert_syntax_node(tree, "", syntax_tree)







    def _insert_syntax_node(self, tree, parent_id, node):



        item_id = tree.insert(



            parent_id,



            "end",



            text=str(node),



            open=True



        )







        children = getattr(node, "children", [])







        for child in children:



            self._insert_syntax_node(tree, item_id, child)







    def _open_semantic_tree_window(self, semantic_tree):

        """

        Abre una ventana independiente para mostrar

        el AST con anotaciones semánticas.

        """

        previous_window = getattr(self, "_semantic_tree_window", None)



        if previous_window is not None:

            try:

                if previous_window.winfo_exists():

                    previous_window.destroy()

            except tk.TclError:

                pass



        window = tk.Toplevel(self.root)

        self._semantic_tree_window = window

        window.title("Árbol Sintáctico con Anotaciones Semánticas")

        window.geometry("950x650")



        def close_window():

            self._semantic_tree_window = None

            window.destroy()



        window.protocol("WM_DELETE_WINDOW", close_window)



        container = ttk.Frame(window)

        container.pack(fill=tk.BOTH, expand=True)



        tree = ttk.Treeview(container)

        tree.heading("#0", text="AST con Anotaciones Semánticas", anchor="w")



        y_scroll = ttk.Scrollbar(container, orient=tk.VERTICAL, command=tree.yview)

        x_scroll = ttk.Scrollbar(container, orient=tk.HORIZONTAL, command=tree.xview)



        tree.configure(

            yscrollcommand=y_scroll.set,

            xscrollcommand=x_scroll.set

        )



        tree.grid(row=0, column=0, sticky="nsew")

        y_scroll.grid(row=0, column=1, sticky="ns")

        x_scroll.grid(row=1, column=0, sticky="ew")



        container.rowconfigure(0, weight=1)

        container.columnconfigure(0, weight=1)



        self._insert_semantic_node(tree, "", semantic_tree)





    def _insert_semantic_node(self, tree, parent_id, node):

        """

        Inserta un nodo del AST semántico en el Treeview.

        """

        if hasattr(node, "semantic_str"):

            node_text = node.semantic_str()

        else:

            node_text = str(node)



        item_id = tree.insert(

            parent_id,

            "end",

            text=node_text,

            open=True

        )



        children = getattr(node, "children", [])



        for child in children:

            self._insert_semantic_node(tree, item_id, child)





    # ====================================================



    # UI ACTIONS



    # ====================================================







    def _ui_compile_lex(self):



        code = self.text_area.get("1.0", "end-1c")







        self.panels.set_text(self.panels.lexico, "")



        self.panels.set_text(self.panels.err_lex, "")







        try:



            result = Lexer(code).tokenize()



        except Exception as e:



            self.panels.results_notebook.select(0)



            self.panels.set_text(self.panels.lexico, "")



            self.panels.bottom_pane.select(0)



            self.panels.set_text(self.panels.err_lex, f"Error al ejecutar el lexer:\n{e}\n")



            return







        if isinstance(result, tuple) and len(result) == 2:



            tokens, errors = result



        else:



            tokens = result



            errors = []







        token_lines = []



        token_lines.append("TIPO\tLEXEMA\tLINEA\tCOLUMNA")



        token_lines.append("-" * 60)







        for token in tokens:



            token_type = getattr(token, "token_type", getattr(token, "type", ""))



            if hasattr(token_type, "name"):



                token_type = token_type.name







            lexeme = getattr(token, "lexeme", "")



            line = getattr(token, "line", "")



            column = getattr(token, "column", "")







            token_lines.append(f"{token_type}\t{lexeme}\t{line}\t{column}")







        if len(tokens) == 0:



            tokens_text = "Sin tokens reconocidos.\n"



        else:



            tokens_text = "\n".join(token_lines) + "\n"







        error_lines = []







        for error in errors:



            message = getattr(error, "message", str(error))



            line = getattr(error, "line", "")



            column = getattr(error, "column", "")



            char = getattr(error, "character", None)







            if char is not None and char != "":



                error_lines.append(f"{message} Línea: {line}, columna: {column}, carácter: {char!r}")



            else:



                error_lines.append(f"{message} Línea: {line}, columna: {column}")







        if len(error_lines) == 0:



            errors_text = "Sin errores léxicos.\n"



        else:



            errors_text = "\n".join(error_lines) + "\n"







        self.panels.results_notebook.select(0)



        self.panels.set_text(self.panels.lexico, tokens_text)







        self.panels.bottom_pane.select(0)



        self.panels.set_text(self.panels.err_lex, errors_text)







        self._apply_syntax_highlighting()







    def _ui_compile_syn(self):



        code = self.text_area.get("1.0", "end-1c")







        self.panels.results_notebook.select(1)



        self.panels.set_text(self.panels.sintactico, "")



        self._set_syntax_error_output("")



        self._set_lexical_error_output("")







        try:



            result = Lexer(code).tokenize()







            if isinstance(result, tuple) and len(result) == 2:



                tokens, lexical_errors = result



            else:



                tokens = result



                lexical_errors = []







            if lexical_errors:



                lexical_error_lines = []







                for error in lexical_errors:



                    message = getattr(error, "message", str(error))



                    line = getattr(error, "line", "")



                    column = getattr(error, "column", "")



                    character = getattr(error, "character", "")







                    lexical_error_lines.append(



                        f"{message} Línea: {line}, columna: {column}, carácter: {character!r}"



                    )







                lexical_errors_text = "\n".join(lexical_error_lines) + "\n"







                self.panels.set_text(



                    self.panels.sintactico,



                    "No se ejecutó el análisis sintáctico porque existen errores léxicos.\n\n"



                    "Corrige primero los errores léxicos y vuelve a intentar.\n"



                )







                self._set_lexical_error_output(lexical_errors_text)



                return







            parser = Parser(tokens)



            syntax_tree = parser.parse()







            syntax_text = "Análisis sintáctico correcto.\n\n"



            syntax_text += syntax_tree.to_text()







            self.panels.results_notebook.select(1)



            self.panels.set_text(self.panels.sintactico, syntax_text)



            self._set_syntax_error_output("Sin errores sintácticos.\n")







            self._open_syntax_tree_window(syntax_tree)







        except SyntaxErrorCompiler as error:



            error_text = str(error) + "\n"







            self.panels.results_notebook.select(1)



            self.panels.set_text(



                self.panels.sintactico,



                "Se encontraron errores sintácticos.\n\n"



                "Revisa la pestaña de errores sintácticos.\n"



            )







            self._set_syntax_error_output(error_text)







        except Exception as error:



            self.panels.results_notebook.select(1)



            self.panels.set_text(



                self.panels.sintactico,



                "Error inesperado al ejecutar el análisis sintáctico:\n\n"



                + str(error)



                + "\n"



            )







    def _ui_compile_sem(self):

        """Run the full semantic pipeline and display its real results."""

        code = self.text_area.get("1.0", "end-1c")

        self.panels.results_notebook.select(2)

        self.panels.set_text(self.panels.lexico, "")

        self.panels.set_text(self.panels.sintactico, "")

        self.panels.set_text(self.panels.semantico, "")

        self._set_symbol_table_output([])

        self._set_lexical_error_output("")

        self._set_syntax_error_output("")

        self._set_semantic_error_output("")



        previous_window = getattr(self, "_semantic_tree_window", None)

        if previous_window is not None:

            try:

                if previous_window.winfo_exists():

                    previous_window.destroy()

            except tk.TclError:

                pass

            self._semantic_tree_window = None



        try:

            lexer_result = Lexer(code).tokenize()

        except Exception as error:

            message = f"Error inesperado al ejecutar el lexer:\n{error}\n"

            self.panels.set_text(

                self.panels.semantico,

                "No se ejecutó el análisis semántico porque falló el lexer.\n",

            )

            self._set_syntax_error_output(

                "No se ejecutó el análisis sintáctico.\n"

            )

            self._set_semantic_error_output(

                "No se ejecutó el análisis semántico.\n"

            )

            self._set_lexical_error_output(message)

            return



        if isinstance(lexer_result, tuple) and len(lexer_result) == 2:

            tokens, lexical_errors = lexer_result

        else:

            tokens = lexer_result

            lexical_errors = []



        if lexical_errors:

            error_lines = []

            for error in lexical_errors:

                message = getattr(error, "message", str(error))

                line = getattr(error, "line", "")

                column = getattr(error, "column", "")

                character = getattr(error, "character", "")

                error_lines.append(

                    f"{message} Línea: {line}, columna: {column}, "

                    f"carácter: {character!r}"

                )



            self.panels.set_text(

                self.panels.semantico,

                "No se ejecutó el análisis semántico porque existen "

                "errores léxicos.\n",

            )

            self.panels.set_text(

                self.panels.sintactico,

                "No se ejecutó el análisis sintáctico porque existen "

                "errores léxicos.\n",

            )

            self._set_syntax_error_output(

                "No se ejecutó el análisis sintáctico porque existen "

                "errores léxicos.\n"

            )

            self._set_semantic_error_output(

                "No se ejecutó el análisis semántico.\n"

            )

            self._set_lexical_error_output("\n".join(error_lines) + "\n")

            return



        self._set_lexical_error_output("Sin errores léxicos.\n")



        try:

            syntax_tree = Parser(tokens).parse()

        except SyntaxErrorCompiler as error:

            self.panels.set_text(

                self.panels.sintactico,

                "Se encontraron errores sintácticos.\n\n"

                "Revisa la pestaña de errores sintácticos.\n",

            )

            self.panels.set_text(

                self.panels.semantico,

                "No se ejecutó el análisis semántico porque existen "

                "errores sintácticos.\n",

            )

            self._set_semantic_error_output(

                "No se ejecutó el análisis semántico.\n"

            )

            self._set_syntax_error_output(str(error) + "\n")

            return

        except Exception as error:

            message = (

                "Error inesperado al ejecutar el análisis sintáctico:\n"

                f"{error}\n"

            )

            self.panels.set_text(self.panels.sintactico, message)

            self.panels.set_text(self.panels.semantico, message)

            self._set_semantic_error_output(

                "No se ejecutó el análisis semántico.\n"

            )

            self._set_syntax_error_output(message)

            return



        self._set_syntax_error_output("Sin errores sintácticos.\n")

        self.panels.set_text(

            self.panels.sintactico,

            "Análisis sintáctico correcto.\n\n" + syntax_tree.to_text(),

        )



        try:

            result = SemanticAnalyzer().analyze(syntax_tree)

        except Exception as error:

            message = (

                "Error inesperado al ejecutar el análisis semántico:\n"

                f"{error}\n"

            )

            self.panels.set_text(self.panels.semantico, message)

            self._set_semantic_error_output(message)

            return



        semantic_errors = result.errors.get_objects()

        self._set_symbol_table_output(result.symbol_table.get_all())



        if semantic_errors:

            summary = (

                "Análisis semántico completado con "

                f"{len(semantic_errors)} error(es).\n\n"

            )

            error_text = "\n".join(str(error) for error in semantic_errors) + "\n"

        else:

            summary = "Análisis semántico correcto.\n\n"

            error_text = "Sin errores semánticos.\n"



        semantic_text = summary + result.annotated_ast.to_semantic_text()

        self.panels.set_text(self.panels.semantico, semantic_text)

        self._set_semantic_error_output(error_text)

        self.panels.results_notebook.select(2)

        self._open_semantic_tree_window(result.annotated_ast)





    def _ui_compile_ir(self):



        self.panels.results_notebook.select(3)



        self.panels.set_text(self.panels.intermedio, "Codigo Intermedio (placeholder)\n")







    def _ui_run(self):



        self.panels.bottom_pane.select(3)



        self.panels.set_text(self.panels.exec_out, "Ejecucion (placeholder)\n")







    def _ui_pause(self):



        self.panels.bottom_pane.select(3)



        self.panels.set_text(self.panels.exec_out, "Pausa (placeholder)\n")







    def _ui_stop(self):



        self.panels.bottom_pane.select(3)



        self.panels.set_text(self.panels.exec_out, "Detener (placeholder)\n")
