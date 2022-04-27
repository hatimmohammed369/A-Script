# KEYWORDS / OPERATORS / ...
# You know, those sorts of things
import re

KEYWORDS = (
    "import",
    "from",
    "define",
    "mut",
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
    'from',
    'function',
    'if',
    'import',
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
    'mut',
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

SEPARATORS = ("{", "}", "[", "]", "(", ")", ",", ":", ";", "=>")

BINARY_NUMBER_PATTERN = re.compile(r"0[bB]([_]{0,1}[01]+)+")

OCTAL_NUMBER_PATTERN = re.compile(r"0[oO]([_]{0,1}[0-7]+)+")

HEX_NUMBER_PATTERN = re.compile(r"0[xX]([_]{0,1}[0-9a-fA-F]+)+")

INT_PATTERN = re.compile(r"\d+([_]\d+)*")

FLOAT_PATTERN = re.compile(
    # Integer part with optional fractional part
    r"("

        r"\d+([_]\d+)*" # Integer part

        r"("

            r"[.](\d+([_]\d+)*){0,1}" # Fractional part with optional digits after the decimal point (e.g, .1234, or just ., like in 4.)

            r"|" # OR

            r"[Ee][+-]{0,1}\d+([_]\d+)*" # Exponent part (e-3, E+12)

            r"|" # OR BOTH

            r"[.](\d+([_]\d+)*){0,1}[Ee][+-]{0,1}\d+([_]\d+)*"

        r")"

    r")"

    r"|"

    # No integer part and a fractional part
    r"("

        r"[.]\d+([_]\d+)*([Ee][+-]{0,1}\d+([_]\d+)*){0,1}"

    r")"
)

NUMBER_PATTERN = re.compile(FLOAT_PATTERN.pattern + "|" + INT_PATTERN.pattern)

CHAR_PATTERN = re.compile(pattern=r"'(\\(\\|'|[abfnrtv]|x\d{2})|.)'")

STRING_PATTERN = r'".*?(?<!\\)"'

SINGLE_LINED_STRING_PATTERN = re.compile(pattern = STRING_PATTERN) # Match (matching ") ONLY IF this (matching ") is not preceded by \

MULTI_LINED_STRING_PATTERN  = re.compile(pattern = STRING_PATTERN, flags = re.DOTALL)

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
    r"=>" # Function Return Type
    + "|"
    + r";"
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
