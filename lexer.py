#!/usr/local/bin/python3.10

import re
from typing import Tuple, List, Dict
from dataclasses import dataclass
from const import *
from os import path
from sys import stderr

####################################################################################################

# Tokenizer: takes texts and turns it into "words" (tokens)


@dataclass(init=True, repr=True)
class Line:
    value: str = "" # Actual text excluding \n (line breaks)
    begin: int = 0 # nearest line break when searching backwards
    end: int = 0 # nearest line break when searching forwards


@dataclass(init=True, repr=True, eq=True)
class Token:
    name: str = ""
    value: str = ""

    begin_idx: int = 0
    end_idx: int = 0

    begin_col: int = 0
    end_col: int = 0

    begin_ln: int = 0
    end_ln: int = 0

    def __repr__(self):
        self_idx = f"{self.begin_idx}-{self.end_idx}"
        self_col = f"{self.begin_col}-{self.end_col}"
        self_ln  = str(self.begin_ln) if self.begin_ln == self.end_ln else f"{self.begin_ln}-{self.end_ln}"
        return f"Token({self.name}, {repr(self.value)}, ({self_idx}, {self_col}, {self_ln}))"

    __str__ = __repr__


class Lexer:
    def __init__(
        self,
        file_name:str,
        text: str,  # Text to be tokenized
        indent_type=" ",  # which character to use for indentation,
        # if indent_type.lower() == "s" then we use spaces for indentation
        # if indent_type.lower() == "t" then we use tabs for indentation
        indent_size=4,  # How many indent characters in a single indent token
        supplied_spaces_explicitly=False,  # Did you supply --spaces explicitly?
    ):
        self.file = file_name
        self.text: str = text
        if not self.text.endswith("\n"):
            self.text += "\n"

        self.idx, self.ln, self.col = 0, 0, 0

        self.tokens: list[Token] = []

        self.indents_stack = []  # how many indents currently
        self.indents_tokens_stack: List[Token] = []
        self.checked_indent_in_current_line = False

        self.lines: Dict[int, Line] = {}
        old_idx, idx, ln = 0, 0, 0
        while idx != len(self.text):
            if self.text[idx] == "\n":
                self.lines[ln] = Line(value = self.text[old_idx : idx + 1], begin = old_idx, end = idx + 1)
                ln += 1
                old_idx = idx + 1
            idx += 1
        del old_idx, idx, ln

        self.current_line_obj = self.lines.get(0, None)

        self.indent_type: str = indent_type.lower()
        if self.indent_type not in (" ", "\t"):
            raise ValueError(f'{self.indent_type = } must be either " " or "\\t"')

        self.indent_size = indent_size

        # becomes True after this instance successfully executes tokenize()
        self.done = False

        self.supplied_spaces_explicitly = supplied_spaces_explicitly

        # Store left parentheses "( or [" tokens to enable multi-line statements
        self.left_parenthesis_stack: List[Token] = []

        self.indent_name = "space" if self.indent_type == " " else "tab"

        self.indent_char = "+" if self.indent_name == "space" else "*"


    def pos(self) -> str:
        return self.current_line_obj.value + " " * self.col + "^"


    def advance(self, steps):
        self.idx = min(self.idx + steps, len(self.text))
        self.col = self.col + steps
        return self


    def generate_next_token(self) -> Tuple[str, Token]:
        tok = None
        error = ""
        current_line = self.current_line_obj.value
        current_char = self.text[self.idx]
        steps = None

        # INDENTATION
        if not self.checked_indent_in_current_line and not self.left_parenthesis_stack and self.col == 0:
            self.checked_indent_in_current_line = True
            captured_indent = re.match(pattern = r"[ \t]*", string = current_line).group()

            # first_non_white_space will never be None because empty/white-spaces lines are not checked for indentation
            # so it's always guaranteed we have at least one non-white-space in current line
            first_non_white_space = re.search(pattern = r"[^\s]", string = current_line).group()
            if first_non_white_space not in ("#", ")", "}", "]"):
                if (" " in captured_indent and self.indent_name == "tab") or ("\t" in captured_indent and self.indent_name == "space"):
                    # Mixing tabs an spaces
                    error += f"Indentation Error in \"{self.file}\", line {self.ln + 1}, column {self.col + 1}:\n"
                    error += " " * 4 + "Mixing tabs and spaces in indentation\n"
                    error += f"{self.ln + 1} | " + "".join("*" if c == "\t" else "+" for c in captured_indent)
                    error += current_line[len(captured_indent) : ]
                    error += " " * len(f"{self.ln + 1} | ")
                    illegar_chars = 0
                    for c in captured_indent:
                        if c != self.indent_type:
                            illegar_chars += 1
                            error += "^"
                        else:
                            error += " "
                    error += "\n"
                    error += " " * len(f"{self.ln + 1} | ") + f"Found {'one' if illegar_chars == 1 else illegar_chars} "
                    error += f"{'tab' if self.indent_name == 'space' else 'space'}{'s' if illegar_chars > 1 else ''}\n\n"
                    error += "In every indent in this file, remove ALL "
                    error += f"{'TAB' if self.indent_name == 'space' else 'SPACE'}S"

                if not error:
                    current_indent = 0 if not self.indents_stack else self.indents_stack[-1]
                    tok = Token(
                        value     = captured_indent,
                        begin_idx = self.idx,
                        begin_col = self.col,
                        begin_ln  = self.ln,
                        end_ln    = self.ln
                    )
                    if len(captured_indent) < current_indent:
                        # OUTDENT
                        tok.name = "OUTDENT"
                        self.indents_stack.pop(-1)
                    elif current_indent < len(captured_indent):
                        # INDENT
                        tok.name = "INDENT"
                        self.indents_stack.append(len(tok.value))
                    else:
                        # No INDENT/DEDEN, just advance
                        tok = None

                    if tok:
                        self.indents_tokens_stack.append(tok)
            # end "if first_non_white_space not in ("#", ")", "}", "]")"
            steps = len(captured_indent)

        # COMMENTS
        elif current_char == "#":
            tok = Token(
                begin_idx = self.idx,
                begin_col = self.col,
                begin_ln  = self.ln,
            )

            if multi_lined_comment := re.compile(pattern = r"##.*##", flags = re.DOTALL).match(
                string = self.text,
                pos    = self.idx,
            ):
                # MULTI LINED COMMENT
                tok.name  = "MULTI_LINED_COMMENT"
                tok.value = multi_lined_comment.group()
                tok.end_col = -1
                for c in reversed(tok.value):
                    if c == "\n":
                        break
                    else:
                        tok.end_col += 1
                tok.end_ln = tok.begin_ln + tok.value.count("\n")
            else:
                # SINGLE LINE COMMENT
                tok.name    = "COMMENT"
                tok.value   = current_line[self.col : ].removesuffix("\n") # exclude (\n)
                tok.end_col = tok.begin_col + len(tok.value)
                tok.end_ln  = tok.begin_ln
            tok.end_idx = tok.begin_idx + len(tok.value)

        # LINE BREAK
        elif current_char == "\n":
            tok = Token(
                name      = "LINE_BREAK",
                value     = "\n",
                begin_idx = self.idx,
                begin_col = self.col,
                begin_ln  = self.ln,
                end_ln    = self.ln
            )
            tok.end_idx = tok.begin_idx + len(tok.value)
            tok.end_col = tok.begin_col + len(tok.value)

        # NAME/KEYWORD
        elif name_keyword_match := NAME_PATTERN.match(string = current_line, pos = self.col):
            tok = Token(
                value     = name_keyword_match.group(),
                begin_idx = self.idx,
                begin_col = self.col,
                begin_ln  = self.ln,
                end_ln    = self.ln
            )
            tok.end_idx = tok.begin_idx + len(tok.value)
            tok.end_col = tok.begin_col + len(tok.value)
            if tok.value in KEYWORDS:
                tok.name = "KEYWORD"
            else:
                tok.name = "NAME"

        # NUMBER
        elif number_match := NUMBER_PATTERN.match(string = current_line, pos = self.col):
            tok = Token(
                value     = number_match.group(),
                begin_idx = self.idx,
                begin_col = self.col,
                begin_ln  = self.ln,
                end_ln    = self.ln
            )
            tok.end_idx = tok.begin_idx + len(tok.value)
            tok.end_col = tok.begin_col + len(tok.value)
            if INT_PATTERN.match(tok.value):
                tok.name = "INT::"
            else:
                tok.name = "FLOAT::"
            tok.name += "NUMBER"

        # OPERATORS
        elif operator_match := OPERATOR_PATTERN.match(string = current_line, pos = self.col):
            tok = Token(
                name      = "OPERATOR",
                value     = operator_match.group(),
                begin_idx = self.idx,
                begin_col = self.col,
                begin_ln  = self.ln,
                end_ln    = self.ln
            )
            tok.end_idx = tok.begin_idx + len(tok.value)
            tok.end_col = tok.begin_col + len(tok.value)

        # SEPARATORS
        elif separator_match := SEPARATOR_PATTERN.match(string = current_line, pos = self.col):
            tok = Token(
                name      = "SEPARATOR",
                value     = separator_match.group(),
                begin_idx = self.idx,
                begin_col = self.col,
                begin_ln  = self.ln,
                end_ln    = self.ln
            )
            tok.end_idx = tok.begin_idx + len(tok.value)
            tok.end_col = tok.begin_col + len(tok.value)
            if tok.value in ("(", "{", "["):
                self.left_parenthesis_stack.append(tok)
            elif tok.value in (")", "}", "]"):
                if self.left_parenthesis_stack:
                    self.left_parenthesis_stack.pop(-1)
                else:
                    first_non_white_space = re.search(pattern = r"[^\s]", string = current_line).start()
                    error += f"Syntax Error in \"{self.file}\", line {self.ln + 1}, column {self.col + 1}:\n"
                    error += " " * 4 + f"Un-expected {tok.value}\n"
                    error += f"{self.ln + 1} | " + current_line.strip() + "\n"
                    error += " " * len(f"{self.ln + 1} | ") + " " * (self.col - first_non_white_space) + "^" + "\n"

        # CHARACTERS
        elif current_char == "'":
            weak_match = re.compile(pattern = r"['].*(?<!\\)[']").match(string = current_line, pos = self.col)
            first_non_white_space = re.search(pattern = r"[^\s]", string = current_line).start()
            if weak_match:
                if char_match := CHAR_PATTERN.match(string = weak_match.group()):
                    tok = Token(
                        name      = "CHARACTER",
                        value     = char_match.group(),
                        begin_idx = self.idx,
                        begin_col = self.col,
                        begin_ln  = self.ln,
                        end_ln    = self.ln
                    )
                    tok.end_idx = tok.begin_idx + len(tok.value)
                    tok.end_col = tok.begin_col + len(tok.value)
                else:
                    # Invalid character
                    error += f"Syntax Error in \"{self.file}\", line {self.ln + 1}, column {self.col + 1}:\n"
                    error += " " * 4 + "Invalid character\n"
                    error += f"{self.ln + 1} | " + current_line.strip() + "\n"
                    error += " " * len(f"{self.ln + 1} | ") + " " * (self.col - first_non_white_space)
                    error += "^" * len(weak_match.group()) + "\n"

            else:
                # Un-terminated character
                error += f"Syntax Error in \"{self.file}\", line {self.ln + 1}, column {self.col + 1}:\n"
                error += " " * 4 + "Un-terminated character\n"
                error += f"{self.ln + 1} | " + current_line.strip() + "\n"
                error += " " * len(f"{self.ln + 1} | ") + " " * (self.col - first_non_white_space) + "^" + "\n"
                error += "Close this ' by adding another '\n"

        # STRINGS
        elif current_char == '"':
            tok = Token(
                begin_idx = self.idx,
                begin_col = self.col,
                begin_ln  = self.ln,
            )

            if single_lined_string := SINGLE_LINED_STRING_PATTERN.match(string = current_line, pos = self.col):
                # SINGLE LINE STRING
                tok.name    = "STRING"
                tok.value   = single_lined_string.group()
                tok.end_col = tok.begin_col + len(tok.value)
                tok.end_ln  = tok.begin_ln
            elif multi_lined_string := MULTI_LINED_STRING_PATTERN.match(string = self.text, pos = self.idx):
                # MULTI LINED STRING
                tok.name  = "MULTI_LINED_STRING"
                tok.value = multi_lined_string.group()
                tok.end_col = -1
                for c in reversed(tok.value):
                    if c == "\n":
                        break
                    else:
                        tok.end_col += 1
                tok.end_ln = tok.begin_ln + tok.value.count("\n")
            else:
                # Un-terminated string
                first_non_white_space = re.search(pattern = r"[^\s]", string = current_line).start()
                error += f"Syntax Error in \"{self.file}\", line {self.ln + 1}, column {self.col + 1}:\n"
                error += " " * 4 + "Un-terminated string\n"
                error += f"{self.ln + 1} | " + current_line.strip() + "\n"
                error += " " * len(f"{self.ln + 1} | ") + " " * (self.col - first_non_white_space) + "^" + "\n"

            tok.end_idx = tok.begin_idx + len(tok.value)


        if not error:
            if not steps: # WE DID NOT CHECK FOR INDENTATION, WE DID SOMETHING ELSE
                if tok:
                    steps = len(tok.value)

            if steps:
                if (
                    not tok # There's no change in indentation
                    or
                    tok and not tok.name.startswith("MULTI_LINED") # A Valid none MULTI_LINED token
                ):
                    # using self.advance when encountering MULTI_LINED_STRING/MULTI_LINED_COMMENT is dangerous
                    # since self.col becomes invalid after call to self.advance
                    self.advance(steps)
        return error, tok


    def generate_tokens(self):
        useless_white_space_pattern = re.compile(pattern = r"(?!\n)\s")
        error = ""
        if not self.done:
            while True: # Iterate lines
                self.current_line_obj = self.lines.get(self.ln, None)
                if not self.current_line_obj:
                    self.ln -= 1
                    self.current_line_obj = self.lines[self.ln]
                    break
                line_value = self.current_line_obj.value
                if not (
                    (last_tok := None if not self.tokens else self.tokens[-1]) and last_tok.name.startswith("MULTI_LINED")
                ):
                    self.col = 0

                    # If multi-lining is ON, assume we checked for indentation
                    # because there's no indentation when multi-lining
                    self.checked_indent_in_current_line = bool(self.left_parenthesis_stack)
                else:
                    self.checked_indent_in_current_line = True
                tok = None
                if len(line_value) != 0:
                    current_position_is_indentation = not self.checked_indent_in_current_line # True when at line head, False otherwise
                    while True: # Generate all tokens in current line
                        if (
                            self.col == 0 and
                            re.fullmatch(
                                pattern = rf"{useless_white_space_pattern.pattern}+",
                                string = line_value.removesuffix("\n")
                            )
                        ):
                            # WHITE-SPACES LINE
                            self.advance(steps = len(line_value.removesuffix("\n"))) # exclude \n
                            # We need to reach this line's (\n), not overcome it
                            # so advance the last item in this line, which is \n
                        else:
                            if useless_white_space_pattern.match(string = self.text[self.idx]) and not current_position_is_indentation:
                                if (
                                    (self.col == 0 and self.left_parenthesis_stack) or
                                    (self.col != 0 and self.col < len(line_value))
                                ):
                                    stop = re.compile(pattern = r"[^\s]|\n").search(
                                        string = line_value,
                                        pos    = self.col + 1,
                                        endpos = len(line_value)
                                    )
                                    if stop:
                                        steps = len(stop.group())
                                    else:
                                        steps = len(line_value) - self.idx
                                    self.advance(steps)
                            else:
                                error, tok = self.generate_next_token()
                                if error:
                                    print(error, file = stderr)
                                    exit(1)
                                else:
                                    # We moved beyond line head, indentation no longer exist
                                    current_position_is_indentation = False
                                    if tok:
                                        self.tokens.append(tok)
                                        if tok.value == "\n" or tok.name.startswith("MULTI_LINED"):
                                            break
                    # end "while True" generate all tokens in current line
                # Done processing
                if not tok or tok.value == "\n":
                    self.ln += 1
                else:
                    self.idx = tok.end_idx
                    self.col = tok.end_col + 1
                    self.ln  = tok.end_ln
            # end "while True" Iterate all lines

            current_line = self.current_line_obj.value

            left_open_parenthesis = False
            if self.left_parenthesis_stack:
                last_left = self.left_parenthesis_stack[-1]
                error_line = self.lines[last_left.begin_ln].value
                first_non_white_space = re.search(pattern = r"[^\s]", string = error_line).start()

                error += f"Syntax Error in \"{self.file}\", line {last_left.begin_ln + 1}, column {last_left.begin_col + 1}:\n"
                error += " " * 4 + f"Un-closed {last_left.value}\n"
                error_line_indent = re.match(pattern = r"[ \t]*", string = error_line).group()

                error += f"{last_left.begin_ln + 1} | " + "..." * int(len(error_line_indent) > self.indent_size)
                error += (" " * self.indent_size) * int(bool(error_line_indent)) + error_line.strip() + "\n"
                error += " " * len(f"{last_left.begin_ln + 1} | ")
                error += (" " * 3) * int(len(error_line_indent) > self.indent_size)
                error += (" " * self.indent_size) * int(bool(error_line_indent))
                error += " " * (last_left.begin_col - first_non_white_space) + "^" + "\n"
                left_open_parenthesis = True

            if not left_open_parenthesis and self.indents_stack:
                if error:
                    error += "\n"
                    error += "<===========================================================================>\n"
                    error += "\n"
                error += f"Indentation Error in \"{self.file}\", line {self.ln + 1}, column {self.col + 1}:\n"
                error += " " * 4 + "Expected (end) statement\n\n"
                error += f"HELP: Add (end) after line {self.ln + 1} like below:\n\n"
                current_line_indent = re.match(pattern = r"[ \t]*", string = current_line).group()

                error += f"{self.ln + 1} | " + "..." * int(len(current_line_indent) > self.indent_size)
                error += (" " * self.indent_size) * int(bool(current_line_indent)) + current_line.strip() + "\n"
                error += f"{self.ln + 2} | " + "end" + "\n"
                error += " " * len(f"{self.ln + 2} | ") + "+++" + "\n"

            if error:
                print(error, file = stderr)
                exit(1)
            else:
                EOF = Token(
                    name  = "EOF",
                    value = "",
                )
                EOF.begin_idx = EOF.end_idx = len(self.text)
                EOF.begin_col = EOF.end_col = self.current_line_obj.end
                EOF.begin_ln  = EOF.end_ln  = self.ln
                self.tokens.append(EOF)

            self.done = True
        return self


    def __iter__(self):
        if self.done is False:
            self.generate_tokens()
        return iter(self.tokens)


if __name__ == "__main__":
    from argparse import ArgumentParser
    from sys import argv

    parser = ArgumentParser()

    parser.add_argument("--source", help="A small code sample to execute")
    parser.add_argument("--file", help="Source file")
    parser.add_argument(
        "--spaces",
        help="Use spaces for indentation, default\n"
        + "In other words, when supplying neither --spaces not --tabs, --spaces is default",
        action="store_true",
        default=True,
    )
    parser.add_argument(
        "--tabs", help="Use tabs for indentation", action="store_true", default=False
    )
    parser.add_argument(
        "--indent_size", help="Indent size", default=4
    )  # this means one indent token equals 4 spaces/tabs

    args = parser.parse_args()
    cmd_line = "".join(argv)

    # Source code
    if args.file:
        source = open(args.file).read()
        file = path.abspath(args.file)
    else:
        source = args.source
        file = "<stdin>"

    # Indent type
    if (
        "--spaces" in argv and "--tabs" in argv
    ):  # both --spaces and --tabs were supplied
        print("You can not use both tabs and spaces indentation, pick one", file = stderr)
        exit(1)

    supplied_spaces_explicitly = False
    if (
        "--spaces" in argv and "--tabs" not in argv
    ):  # --spaces was supplied, --tabs was not
        indent = " "
        supplied_spaces_explicitly = True
    elif (
        "--tabs" in argv and "--spaces" not in argv
    ):  # --tabs was supplied, --spaces was not
        indent = "\t"
        supplied_spaces_explicitly = False
    else:  # neither --spaces nor --tabs, then assume --spaces
        indent = " "  # not supplied
        supplied_spaces_explicitly = False

    # Indent size
    try:
        args.indent_size = int(args.indent_size)
    except:
        print(f"--indent_size '{args.indent_size}' is not a valid positive integer", file = stderr)
        exit(0)

    if args.indent_size <= 0:
        print(f"--indent_size '{args.indent_size}' is not a positive integer", file = stderr)
        exit(0)

    if "--indent_size" in argv:  # --indent_size was supplied, use supplied value
        size = args.indent_size
    else:
        # --indent_size was NOT supplied
        if "--tabs" in argv:  # --tabs only
            size = 1  # Use 1 tab
        else:  # --spaces or (no --spaces and no --tabs)
            size = 4

    if size <= 0:
        print("Please give --indent_size a positive number", file = stderr)
        exit(0)

    tokenizer = Lexer(
        file_name = file,
        text=source,
        indent_type=indent,
        indent_size=size,
        supplied_spaces_explicitly=supplied_spaces_explicitly,
    )
    for token in tokenizer:
        print(token, file = stderr)
