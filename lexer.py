#!/usr/local/bin/python3.10

import re
from typing import Tuple, List, Dict
from dataclasses import dataclass
from const import *
from os import path
from sys import stderr

####################################################################################################

# Tokenizer (aka Lexer): takes texts and turns it into "words" (tokens)


@dataclass(init=True, repr=True)
class Line:
    value: str = "" # Actual text excluding \n (line breaks)
    begin: int = 0 # index of first character in line
    # it can be that begin == end+1, in such case the line empty, it's "\n", the smallest line possible
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
    def __init__(self, file_name : str, text: str):
        self.file   : str = file_name
        self.source : str = text
        if not self.source.endswith("\n"):
            self.source += "\n"

        self.idx, self.ln, self.col = 0, 0, 0

        self.tokens: list[Token] = [] # Stores all generated tokens

        self.indents_stack: List[int] = []  # how many indents currently
        self.indents_tokens_stack: List[Token] = [] # stores all INDENT/OUTDENT tokens

        # True after checking indentation in current line, False only before checking indentation
        self.checked_indent_in_current_line = False

        # if self.source does not end with (\n), then add (\n)
        # this way we can guarantee there's at least one line in every input
        # so there's no way self.lines is empty, and so we can always get self.lines[0]
        self.lines: Dict[int, Line] = {}
        ln = 0
        for line_match in re.finditer(pattern = r".*\n", string = self.source):
            self.lines[ln] = Line(value = line_match.group(), begin = line_match.start(), end = line_match.end())
            ln += 1

        self.current_line_obj = self.lines[0] # self.lines is never empty, so self.current_line_obj always exists

        # becomes True after this instance successfully executes generate_tokens()
        self.done = False

        # Store left parentheses, ( or [ or {, tokens to enable multi-lined statements
        self.left_parenthesis_stack: List[Token] = []


    def pos(self) -> str:
        """
        Give a nice string representation of current position in current line, something like this:
            func_name(0)
                     ^
        """
        return self.current_line_obj.value + " " * self.col + "^"


    def advance(self, steps):
        self.idx = min(self.idx + steps, len(self.source)) # maintain self.idx <= len(self.source)
        self.col = self.col + steps
        return self


    def generate_next_token(self) -> Tuple[str, Token]:
        tok = None
        error = ""
        current_line = self.current_line_obj.value
        current_char = self.source[self.idx]
        steps = None # takes int value only when detecting indentation, None otherwise

        # INDENTATION
        if (
            current_line.removesuffix("\n") and # current line is not empty AND
            not self.checked_indent_in_current_line and # We DID NOT check indentation in current line AND
            not self.left_parenthesis_stack and # Multi-lining is OFF AND
            self.col == 0 # It's line head
        ):
            self.checked_indent_in_current_line = True
            captured_indent = re.match(pattern = r"[ \t]*", string = current_line).group()

            # Empty lines, "\n", can not introduce INDENT tokens because INDENT tokens objects have actual text in their (value) attribute
            # But empty lines can introduce OUTDENT tokens, but syntactically OUTDENT is generated using (end) statement
            # So empty lines MUST not be checked for indentation because they generate no tokens at all
            # A line only made up of white-spaces is skipped and the code jumps to line break (\n) of this white-spaces line

            # first_non_white_space will never be None because empty/white-spaces lines are not checked for indentation
            # so it's always guaranteed we have at least one non-white-space in current line
            first_non_white_space = re.search(pattern = r"[^\s]", string = current_line).group()
            if first_non_white_space not in ("#", ")", "}", "]"):
                # When first non white space is one of #,),},] then multi-lining is ON
                # Except for # because comments don't affect code semantics they can be placed anywhere
                current_indent = 0 if not self.indents_stack else self.indents_stack[-1]
                if len(captured_indent) != current_indent:
                    # Generate token ONLY WHEN there's change in indentation
                    tok = Token(
                        value     = captured_indent,
                        begin_idx = self.idx,
                        begin_col = self.col,
                        begin_ln  = self.ln,
                        end_ln    = self.ln
                    )
                    if len(captured_indent) < current_indent:
                        #  for
                        #      write
                        #  end
                        # ^
                        # OUTDENT
                        tok.name = "OUTDENT"
                        self.indents_stack.pop(-1)
                    elif current_indent < len(captured_indent):
                        # for
                        #     write
                        # ^^^^
                        # INDENT
                        tok.name = "INDENT"
                        self.indents_stack.append(len(tok.value))

                    self.indents_tokens_stack.append(tok)
            # end "if first_non_white_space not in ("#", ")", "}", "]")"
            steps = len(captured_indent)
        # END INDENTATION

        # COMMENTS
        elif current_char == "#":
            tok = Token(
                begin_idx = self.idx,
                begin_col = self.col,
                begin_ln  = self.ln,
            )
            if multi_lined_comment := re.compile(pattern = r"##.*##", flags = re.DOTALL).match(
                string = self.source,
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
        # END COMMENTS

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
                if tok.name in BLOCK_STATEMENTS:
                    tok.name += "::BLOCK_KEYWORD"
                elif tok.name in PRIMITIVE_DATA_TYPES:
                    tok.name += "::DATA_TYPE"
            else:
                tok.name = "NAME"
        # END NAME/KEYWORD

        # NUMBER
        elif number_match := NUMBER_PATTERN.match(string = current_line, pos = self.col):
            tok = Token(
                name      = "NUMBER",
                value     = number_match.group(),
                begin_idx = self.idx,
                begin_col = self.col,
                begin_ln  = self.ln,
                end_ln    = self.ln
            )
            tok.end_idx = tok.begin_idx + len(tok.value)
            tok.end_col = tok.begin_col + len(tok.value)
            if FLOAT_PATTERN.match(tok.value):
                tok.name += "::FLOAT"
            else:
                tok.name += "::INT"
        # END NUMBER

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
            if tok.name == ".":
                tok.name += "::MEMBERSHIP_ACCESS"
            elif tok.name in ("+", "-", "*", "/", "~", "&", "|", "^", ">>", "<<"):
                tok.name += "::ARITHMETIC"
            elif tok.name in ("==", "!=", "<", "<=", ">", ">=", "not", "and", "or"):
                tok.name += "::LOGICAL"
            elif tok.name in (":=", "=", "+=", "-=", "*=", "/=", "~=", "&=", "|=", "^=", ">>=", "<<="):
                tok.name += "::ASSIGNMENT"
        # END OPERATOR

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
        # END SEPARATORS

        # CHARACTERS
        elif current_char == "'":
            weak_match = re.compile(pattern = r"['].*?(?<!\\)[']").match(string = current_line, pos = self.col)
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
        # END CHARACTERS

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
            elif multi_lined_string := MULTI_LINED_STRING_PATTERN.match(string = self.source, pos = self.idx):
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
        # END STRINGS

        if not error:
            if not steps: # WE DID NOT CHECK FOR INDENTATION, WE DID SOMETHING ELSE
                if tok:
                    steps = len(tok.value)

            if steps:
                if (
                    not tok or # There's no change in indentation OR
                    (tok and not tok.name.startswith("MULTI_LINED")) # A Valid non-MULTI_LINED token
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
                    (last_tok := None if not self.tokens else self.tokens[-1]) and # There's at least one token AND
                    last_tok.name.startswith("MULTI_LINED") # It's a MULTI_LINED token
                ):
                    # SO THIS CONDITION IS TRUE WHEN:
                    #    - No tokens available
                    #    - Last generated token IS NOT MULTI_LINED_COMMENT/MULTI_LINED_STRING
                    self.col = 0
                    # If multi-lining is ON, assume we checked for indentation
                    # because there's no indentation when multi-lining
                    self.checked_indent_in_current_line = bool(self.left_parenthesis_stack)
                else:
                    # Last generated token is MULTI_LINED_COMMENT/MULTI_LINED_STRING
                    # this means will start tokenization process from the middle of the line in which
                    # this (Last generated token MULTI_LINED_COMMENT/MULTI_LINED_STRING) ends
                    # and since indentation can not occur in the middle, we assume we check indentation
                    # 1 write("
                    # 2    STRING
                    # 3 ")
                    #    ^
                    # We start from ^, as you can see line head belongs to that MULTI_LINED_STRING, and so there's no indentation
                    # we just assume we checked indentation
                    self.checked_indent_in_current_line = True
                current_position_is_indentation = not self.checked_indent_in_current_line # True when at line head, False otherwise
                while True: # Generate all tokens in current line
                    if (
                        self.col == 0 and # It's line head AND
                        re.fullmatch(     # This line is just white-spaces
                            pattern = rf"{useless_white_space_pattern.pattern}+",
                            string = line_value.removesuffix("\n")
                        )
                    ):
                        # WHITE-SPACES LINE
                        self.advance(steps = len(line_value.removesuffix("\n"))) # exclude \n
                        # We need to reach this line's (\n), not overcome it
                        # so advance to last item in this line, which is \n
                    else:
                        if (
                            # Current char is a useless white-space AND
                            useless_white_space_pattern.match(string = self.source[self.idx]) and
                            # This is not line head so we don't skip indentation as if they're useless white-spaces
                            not current_position_is_indentation
                        ):
                            if (
                                # It's line head but Multi-lining is ON OR
                                (self.col == 0 and self.left_parenthesis_stack) or
                                # We are in the middle of current line
                                self.col != 0 and self.col < len(line_value)
                            ):
                                # THIS CONDITION SAYS MAKE SURE CURRENT POSITION IS NEVER INDENTATION
                                stop = re.compile(pattern = r"[^\s]|\n").search(
                                    string = line_value,
                                    pos    = self.col + 1,
                                    endpos = len(line_value)
                                )
                                # no need to check if (stop) is None because we search for either a non-white-space or \n
                                # each line self.lines ends with (\n), so it's always guaranteed that (stop) will find a match
                                steps = len(stop.group())
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
                                        # 1 - We found (\n) which means we reached current line end OR
                                        # 2 - We found a MULTI_LINED token, and so remaining characters in this line belong to this
                                        # MULTI_LINED token we just found
                                        # - In either case, no more work to be done in current line
                                        # In case 1, jump to next line
                                        # In case 2, jump to the line where this (MULTI_LINED token we just found) ends
                                        break
                # end "while True" generate all tokens in current line

                # no need for (not tok) part because the smallest line possible is "\n"
                # which means we have at least the (\n) token
                # which is the exact token need to break the loop above ([generate al tokens in current line] loop)
                if tok.value == "\n":
                    # We reached the end of current line
                    self.ln += 1
                else:
                    # 1 write("
                    #         +
                    # 2    STRING
                    # 3 ")
                    #    ^
                    # We jump from + to ^
                    # Next token will be )

                    # 1 ##
                    #   +
                    # 2 ANNOYING
                    # 3 MULTI
                    # 4 LINED
                    # 5 COMMENT
                    # 6
                    # 7 ##\n
                    #     ^^
                    # We jump from + to ^^
                    # Next token is (\n)

                    # We found a MULTI_LINED token, we need an abnormal jump
                    self.idx = tok.end_idx # the first character after this MULTI_LINED token
                    self.col = tok.end_col + 1 # the first character after this MULTI_LINED token in end line of this MULTI_LINED
                    self.ln  = tok.end_ln # move to end line of this MULTI_LINED
            # end "while True" Iterate all lines

            current_line = self.current_line_obj.value

            left_open_parenthesis = False
            if self.left_parenthesis_stack:
                # Un-close left parentheses
                # print(
                #      ^
                last_left = self.left_parenthesis_stack[-1]
                error_line = self.lines[last_left.begin_ln].value
                first_non_white_space = re.search(pattern = r"[^\s]", string = error_line).start()

                error += f"Syntax Error in \"{self.file}\", line {last_left.begin_ln + 1}, column {last_left.begin_col + 1}:\n"
                error += " " * 4 + f"Un-closed {last_left.value}\n"
                error_line_indent = re.match(pattern = r"[ \t]*", string = error_line).group()

                error += f"{last_left.begin_ln + 1} | " + "..." * int(len(error_line_indent) > 4)
                error += (" " * 4) * int(bool(error_line_indent)) + error_line.strip() + "\n"
                error += " " * len(f"{last_left.begin_ln + 1} | ")
                error += (" " * 3) * int(len(error_line_indent) > 4)
                error += (" " * 4) * int(bool(error_line_indent))
                error += " " * (last_left.begin_col - first_non_white_space) + "^" + "\n"
                left_open_parenthesis = True

            if not left_open_parenthesis and self.indents_stack:
                if error:
                    error += "\n"
                    error += "<===========================================================================>\n"
                    error += "\n"
                # Missing (end) statement
                # for
                #     write(x)

                # Do this:
                # for
                #     write(x)
                # end
                # +++
                error += f"Indentation Error in \"{self.file}\", line {self.ln + 1}, column {self.col + 1}:\n"
                error += " " * 4 + "Expected (end) statement\n\n"
                error += f"HELP: Add (end) after line {self.ln + 1} like below:\n\n"
                current_line_indent = re.match(pattern = r"[ \t]*", string = current_line).group()

                error += f"{self.ln + 1} | " + "..." * int(len(current_line_indent) > 4)
                error += (" " * 4) * int(bool(current_line_indent)) + current_line.strip() + "\n"
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
                EOF.begin_idx = EOF.end_idx = len(self.source)
                EOF.begin_col = EOF.end_col = self.current_line_obj.end
                EOF.begin_ln  = EOF.end_ln  = self.ln
                self.tokens.append(EOF)

            self.done = True
        # end "if not self.done"
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
        print("You must supply either --file or --source, not both", file = stderr)
        exit(1)

    tokenizer = Lexer(
        file_name = file,
        text=source,
    )
    for token in tokenizer:
        print(token, file = stderr)
