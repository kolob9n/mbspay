"""Formula engine — tokenizer (lexer)."""

import enum
import re
from dataclasses import dataclass
from typing import Optional

from app.shared.formula_engine.exceptions import FormulaSyntaxError


class TokenType(str, enum.Enum):
    NUMBER = "NUMBER"
    VARIABLE = "VARIABLE"
    PLUS = "PLUS"
    MINUS = "MINUS"
    STAR = "STAR"
    SLASH = "SLASH"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    COMMA = "COMMA"
    FUNCTION = "FUNCTION"
    EOF = "EOF"


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str
    position: int  # character offset in source


# ---- Token patterns ---------------------------------------------------------
_TOKEN_SPEC: list[tuple[str, TokenType]] = [
    (r"\d+\.\d+", TokenType.NUMBER),   # decimal
    (r"\d+", TokenType.NUMBER),        # integer
    (r"[A-Z_][A-Z0-9_]*", TokenType.VARIABLE),  # uppercase identifiers
    (r"\+", TokenType.PLUS),
    (r"-", TokenType.MINUS),
    (r"\*", TokenType.STAR),
    (r"/", TokenType.SLASH),
    (r"\(", TokenType.LPAREN),
    (r"\)", TokenType.RPAREN),
    (r",", TokenType.COMMA),
]

# Keywords that are functions, not variables
_FUNCTION_NAMES: set[str] = {"MIN", "MAX", "ROUND", "ABS", "IF"}


def tokenize(source: str) -> list[Token]:
    """Convert a formula string into a list of tokens."""
    tokens: list[Token] = []
    pos = 0
    length = len(source)

    while pos < length:
        # Skip whitespace
        if source[pos].isspace():
            pos += 1
            continue

        matched = False
        for pattern, tok_type in _TOKEN_SPEC:
            m = re.match(pattern, source[pos:])
            if m:
                value = m.group(0)
                # Distinguish functions from variables
                if tok_type == TokenType.VARIABLE and value in _FUNCTION_NAMES:
                    # Peek ahead: if next non-space char is '(', it's a function
                    next_pos = pos + len(value)
                    while next_pos < length and source[next_pos].isspace():
                        next_pos += 1
                    if next_pos < length and source[next_pos] == "(":
                        tok_type = TokenType.FUNCTION

                tokens.append(Token(tok_type, value, pos))
                pos += len(value)
                matched = True
                break

        if not matched:
            raise FormulaSyntaxError(
                f"Неизвестный символ: '{source[pos]}'", position=pos
            )

    tokens.append(Token(TokenType.EOF, "", pos))
    return tokens
