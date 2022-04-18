from dataclasses import dataclass
from typing import Any

# KEYWORDS / OPERATORS / ...
# You know, those sorts of things
import re

KEYWORDS = (
    "define",
    "var",
    "const",
    "int",
    "float",
    "char",
    "string",
    "bool",
    "not",
    "and",
    "or",
    "true",
    "false",
    "array",
    "ref_of",
    "struct",
    "function",
    "return",
    "if",
    "else",
    "else_if",
    "for",
    "in",
    "while",
    "end",
    "break",
    "continue",
    "pass",
)

SORTED_KEYWORDS = (
    'and',
    'array',
    'bool',
    'break',
    'char',
    'const',
    'continue',
    'define',
    'else',
    'else_if',
    'end',
    'false',
    'float',
    'for',
    'function',
    'if',
    'in',
    'int',
    'not',
    'or',
    'pass',
    'ref_of',
    'return',
    'string',
    "struct",
    'true',
    'var',
    'while'
)

BLOCK_STATEMENTS = ("function", "if", "else", "else_if", "for", "while")

PRIMITIVE_DATA_TYPES = ("int", "float", "bool", "char", "string", "array")

OPERATORS = (
    ".", # Membership access
    # ARITHMETIC_OPERATORS
    "+",
    "-",
    "*",
    "/",
    "~",
    "&",
    "|",
    "^",
    ">>",
    "<<",
    # LOGICAL_OPERATORS
    "==",
    "!=",
    "<",
    "<=",
    ">",
    ">=",
    "not",
    "and",
    "or",
    # ASSIGNMENT_OPERATORS
    ":=",
    "=",
    "+=",
    "-=",
    "*=",
    "/=",
    "~=",
    "&=",
    "|=",
    "^=",
    ">>=",
    "<<=",
)

SEPARATORS = ("{", "}", "[", "]", "(", ")", ",", ":", ";")

INT_PATTERN = re.compile(
    r"[+-]{0,1}[0-9]+([eE][+-]{0,1}[0-9]+){0,1}(?![.]([0-9]*[eE][+-]{0,1}[0-9]+|[0-9]+([eE][-+]{0,1}[0-9]+){0,1}))"
)  # Match integer ONLY IF it's NOT before a fractional part (e.g, .2384)
# This ensure INT_PATTERN matches ONLY integers

FLOAT_PATTERN = re.compile(
    r"[+-]{0,1}[0-9]+[.][0-9]*([eE][+-]{0,1}[0-9]+){0,1}|[+-]{0,1}[0-9]*[.][0-9]+([eE][+-]{0,1}[0-9]+){0,1}"
)

NUMBER_PATTERN = re.compile(FLOAT_PATTERN.pattern + "|" + INT_PATTERN.pattern)

CHAR_PATTERN = re.compile(pattern=r"'(\\(\\|'|[abfnrtv]|x\d{2})|.)'")

STRING_PATTERN = re.compile(
    r'".*(?<!\\)"', re.DOTALL
)  # Match (matching ") ONLY IF this (matching ") is not preceded by \
# This way we can strings like "This is "A String" inside another"

NAME_PATTERN = re.compile(r"[_a-zA-Z][_a-zA-Z0-9]*")

OPERATOR_PATTERN = re.compile(
    r"[.]|"
    r"not|"
    r"and|"
    r"or|"
    r"[+][+]|"
    r"[+]=|"
    r"--|"
    r"-=|"
    r"[*]=|"
    r"/=|"
    r"~=|"
    r"&=|"
    r"[|]=|"
    r"\^="
    r">>=|"
    r">>|"
    r"<<=|"
    r"<<=|"
    r":=|"
    r"==|"
    r"!=|"
    r"<=|"
    r">=|"
    r"[+]|"
    r"-|"
    r"[*]|"
    r"/|"
    r"~|"
    r"&|"
    r"[|]|"
    r"\^|"
    r"<|"
    r">|"
    r"="
)

SEPARATOR_PATTERN = re.compile(
    r";"
    + "|"
    + r":"
    + "|"
    + r","
    + "|"
    + r"\["
    + "|"
    + r"]"
    + "|"
    + r"\("
    + "|"
    + r"\)"
    + "|"
    + r"{"
    + "|"
    + r"}"
)

ARRAY_TYPE_PATTERN = re.compile(
    rf"array[ ]*\([ ]*{NAME_PATTERN.pattern}[ ]*([ ]*,[ ]*{INT_PATTERN.pattern}[ ]*)*[ ]*\)"
)
