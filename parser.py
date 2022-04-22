#!/usr/local/bin/python3.10

import re
from typing import Tuple, List, Dict
from dataclasses import dataclass
from const import *
from os import path
from sys import stderr
from lexer import Lexer

####################################################################################################

# Parser: do syntax analysis then outputs syntax tree
class Parser:
    def __init__(self, lexer_object = None):
        self.lexer: Lexer = lexer_object
        self.done = False


    def analyze(self):
        if not self.done:
            pass
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
        print("You must supply either --file or --source, not both", file = stderr)
        exit(1)

    Parser(
        lexer_object = Lexer(
            file_name = file,
            text=source,
        ).generate_tokens()
    ).analyze()
