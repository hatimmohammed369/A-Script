#!/usr/local/bin/python3.10

import re
from typing import Tuple, List, Dict
from dataclasses import dataclass
from const import *
from os import path
from sys import stderr
from lexer import Lexer, Token

####################################################################################################

class ASTNode:
    def __init__(self):
        self.name = ""
        self.tokens: List[Token] = []


class Statement(ASTNode):
    def __init__(self):
        super().__init__()
        self.name += "STATEMENT"


class Simple_Statement(Statement):
    def __init__(self):
        super().__init__()
        self.name += "::SIMPLE_STATEMENT"


class Simple_Statement_Pass(Simple_Statement):
    def __init__(self):
        super().__init__()
        self.name += "::PASS_STATEMNET"


class Simple_Statement_Break(Simple_Statement):
    def __init__(self):
        super().__init__()
        self.name += "::BREAK_STATEMNET"


class Simple_Statement_Continue(Simple_Statement):
    def __init__(self):
        super().__init__()
        self.name += "::CONTINUE_STATEMNET"


class Compound_Statement(Statement):
    def __init__(self):
        super().__init__()
        self.name += "::COMPOUND_STATEMENT"



class Compound_Statement_Import(Statement):
    def __init__(self, file_path_token: Token = None, items_tokens_list: List[Token] = None):
        super().__init__()
        self.name += "::IMPORT_STATEMENT"
        self.file_path_token: Token = file_path_token
        if self.file_path_token:
            self.file_path: str = self.file_path_token.value
        else:
            self.file_path: str = ""
        self.items_tokens: List[Token] = items_tokens_list
        if not self.items_tokens:
            self.items_tokens = []
        self.items: List[str] = []
        for tok in self.items_tokens:
            self.items.append(tok.value)


# Parser: do syntax analysis then outputs syntax tree
class Parser:
    def __init__(self, lexer_object = None):
        self.lexer: Lexer = lexer_object
        self.pos = 0
        self.update_current_token()
        self.done = False


    def update_current_token(self):
        if self.pos < len(self.lexer.tokens):
            self.current_token = self.lexer.tokens[self.pos]
        else:
            self.current_token = None
        return self


    def advance(self):
        self.pos += 1
        self.update_current_token()
        return self


    def parse_simple_statement_pass(self):
        error = ""
        pass_ast = Simple_Statement_Pass()
        failed = True
        if self.current_token.value == "pass":
            pass_ast.tokens.append(self.current_token) # Add keyword (pass) token
            self.advance()
            if self.current_token:
                if self.current_token.value not in (";", "\n"):
                    error += f"Syntax Error in \"{self.lexer.file}\", "
                    error += f"line {self.current_token.begin_ln + 1}, column {self.current_token.begin_col + 1}:\n"
                    error += " " * 4 + "Unexpected token\n"
                    error += f"{self.current_token.begin_ln + 1} | " + self.lexer.lines[self.current_token.begin_ln].value
                    error += " " * len(f"{self.current_token.begin_ln + 1} | ")
                    error += " " * self.current_token.begin_col + "^" * len(self.current_token.value)
                    pass_ast = None
                else:
                    pass_ast.tokens.append(self.current_token)
                    self.advance()
                    failed = False
        else:
            pass_ast = None
        return (error, pass_ast, failed)


    def parse_simple_statement_break(self):
        error = ""
        break_ast = Simple_Statement_Break()
        failed = True
        if self.current_token.value == "break":
            break_ast.tokens.append(self.current_token) # Add keyword (break) token
            self.advance()
            if self.current_token:
                if self.current_token.value not in (";", "\n"):
                    error += f"Syntax Error in \"{self.lexer.file}\", "
                    error += f"line {self.current_token.begin_ln + 1}, column {self.current_token.begin_col + 1}:\n"
                    error += " " * 4 + "Unexpected token\n"
                    error += f"{self.current_token.begin_ln + 1} | " + self.lexer.lines[self.current_token.begin_ln].value
                    error += " " * len(f"{self.current_token.begin_ln + 1} | ")
                    error += " " * self.current_token.begin_col + "^" * len(self.current_token.value)
                    break_ast = None
                else:
                    break_ast.tokens.append(self.current_token)
                    self.advance()
                    failed = False
        else:
            break_ast = None
        return (error, break_ast, failed)


    def parse_simple_statement_continue(self):
        error = ""
        continue_ast = Simple_Statement_Continue()
        failed = True
        if self.current_token.value == "continue":
            continue_ast.tokens.append(self.current_token) # Add keyword (continue) token
            self.advance()
            if self.current_token:
                if self.current_token.value not in (";", "\n"):
                    error += f"Syntax Error in \"{self.lexer.file}\", "
                    error += f"line {self.current_token.begin_ln + 1}, column {self.current_token.begin_col + 1}:\n"
                    error += " " * 4 + "Unexpected token\n"
                    error += f"{self.current_token.begin_ln + 1} | " + self.lexer.lines[self.current_token.begin_ln].value
                    error += " " * len(f"{self.current_token.begin_ln + 1} | ")
                    error += " " * self.current_token.begin_col + "^" * len(self.current_token.value)
                    continue_ast = None
                else:
                    continue_ast.tokens.append(self.current_token) # include ;
                    self.advance()
                    if self.current_token.value == "\n": # include (\n) if possible
                        continue_ast.tokens.append(self.current_token)
                        self.advance()
                    failed = False
        else:
            continue_ast = None
        return (error, continue_ast, failed)


    def parse_simple_statement(self) -> Tuple[str, Simple_Statement, bool]: # Error, AST, Failed to parse simple statement
        pass_error, pass_ast, failed_to_parse_pass = self.parse_simple_statement_pass()
        if pass_error:
            return (pass_error, None, True)
        else:
            if failed_to_parse_pass:
                break_error, break_ast, failed_to_parse_break = self.parse_simple_statement_break()
                if break_error:
                    return (break_error, None, True)
                else:
                    if failed_to_parse_break:
                        continue_error, continue_ast, failed_to_parse_continue = self.parse_simple_statement_continue()
                        if continue_error:
                            return (continue_error, None, True)
                        else:
                            if failed_to_parse_continue:
                                pass
                            else:
                                return ("", continue_ast, False)
                    else:
                        return ("", break_ast, False)
            else:
                return ("", pass_ast, False)
        pass


    def parse_compound_statement_import(self):
        error = ""
        import_ast = None
        failed = True
        if self.current_token.value == "import":
            # Attemp to parse path to file
            import_token = self.current_token
            self.advance()
            if MULTI_LINED_STRING_PATTERN.match(self.current_token.value):
                try:
                    open(self.current_token.value)
                    import_ast = Compound_Statement_Import()
                    import_ast.tokens.append(import_token)
                    failed = False
                except:
                    # Could not open file
                    error += f"File Error in \"{self.lexer.file}\", "
                    error += f"line {self.current_token.begin_ln + 1}, column {self.current_token.begin_col + 1}:\n"
                    error += " " * 4 + f"Could not open file {self.current_token.value}\n"
                    error += f"{self.current_token.begin_ln + 1} | " + self.lexer.lines[self.current_token.begin_ln].value
                    error += " " * len(f"{self.current_token.begin_ln + 1} | ")
                    error += " " * self.current_token.begin_col
                    error += " " * int(self.current_token.value in ("\a", "\b", "\f", "\n", "\r", "\t", "\v"))
                    error += "^" * len(self.current_token.value)
                    import_ast = None
            else:
                # Syntax Error, expected string
                error += f"Syntax Error in \"{self.lexer.file}\", "
                error += f"line {self.current_token.begin_ln + 1}, column {self.current_token.begin_col + 1}:\n"
                error += " " * 4 + "Expected path to file ( something like \"path\\to\\file\" )\n"
                error += f"{self.current_token.begin_ln + 1} | " + self.lexer.lines[self.current_token.begin_ln].value
                error += " " * len(f"{self.current_token.begin_ln + 1} | ")
                error += " " * self.current_token.begin_col
                error += " " * int(self.current_token.value in ("\a", "\b", "\f", "\n", "\r", "\t", "\v"))
                error += "^" * len(self.current_token.value)
                import_ast = None
        return (error, import_ast, failed)

    def parse_compound_statement(self) -> Tuple[str, Compound_Statement, bool]:
        import_error, import_ast, failed_to_parse_import = self.parse_compound_statement_import()
        if import_error:
            return (import_error, None, True)
        else:
            if failed_to_parse_import:
                pass
            else:
                return ("", import_ast, False)
        return None


    def parse_statement(self) -> Tuple[str, Statement]: # Error, AST Tree
        while self.current_token:
            simple_statement = self.parse_simple_statement()
            if simple_statement:
                simple_error, simple_ast, simple_failed = simple_statement
                if simple_error:
                    return (simple_error, None)
                else:
                    return ("", simple_ast)
            else:
                compound_statement = self.parse_compound_statement()
                if compound_statement:
                    compound_error, compound_ast, compound_failed = compound_statement
                    if compound_error:
                        return (compound_error, None)
                    else:
                        return ("", compound_ast)
                else:
                    break
        return ("", None)


    def parse(self):
        if not self.done:
            while self.current_token:
                if self.current_token.name == "EOF" and self.current_token.end_idx == len(self.lexer.source):
                    break

                if self.current_token.value == "\n":
                    self.advance()

                statement_error, statement_ast = self.parse_statement()
                if statement_error:
                    print(statement_error, file = stderr)
                    exit(1)
                else:
                    if statement_ast:
                        print(statement_ast)
                        print(statement_ast.tokens, "\n")
            self.done = True
        # end "if not self.done"
        return self


if __name__ == "__main__":
    from argparse import ArgumentParser
    from sys import argv

    parser = ArgumentParser()

    parser.add_argument("--source", help="A small code sample to execute")
    parser.add_argument("--file", help="Source file")

    args = parser.parse_args()
    cmd_line = "".join(argv)

    # Source code
    if args.file and args.source:
        print("Do not supply both --file and --source", file = stderr)
        exit(1)
    if args.file and not args.source:
        source = open(args.file).read()
        file = path.abspath(args.file)
    elif args.source and not args.file:
        source = args.source
        file = "<stdin>"
    else:
        print("You must supply either --file or --source", file = stderr)
        exit(1)

    Parser(
        lexer_object = Lexer(
            file_name = file,
            text=source,
        ).generate_tokens()
    ).parse()
