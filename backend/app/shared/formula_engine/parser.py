"""Formula engine — recursive-descent parser.

Grammar:
    expression  = term (('+' | '-') term)*
    term        = factor (('*' | '/') factor)*
    factor      = NUMBER
                | VARIABLE
                | FUNCTION '(' [expression (',' expression)*] ')'
                | '(' expression ')'
                | '-' factor
"""

from decimal import Decimal

from app.shared.formula_engine.ast_nodes import (
    BinaryOpNode,
    ExprNode,
    FunctionNode,
    NumberNode,
    UnaryOpNode,
    VariableNode,
)
from app.shared.formula_engine.exceptions import FormulaSyntaxError
from app.shared.formula_engine.tokens import Token, TokenType, tokenize


class Parser:
    """Recursive-descent parser for formula expressions."""

    def __init__(self, source: str) -> None:
        self._tokens = tokenize(source)
        self._pos = 0

    def parse(self) -> ExprNode:
        """Parse the full expression and return the AST root."""
        node = self._expression()
        self._expect(TokenType.EOF)
        return node

    # ---- Helpers -----------------------------------------------------------

    @property
    def _current(self) -> Token:
        return self._tokens[self._pos]

    def _advance(self) -> Token:
        tok = self._current
        if tok.type != TokenType.EOF:
            self._pos += 1
        return tok

    def _expect(self, expected: TokenType) -> Token:
        tok = self._current
        if tok.type != expected:
            raise FormulaSyntaxError(
                f"Ожидался '{expected.value}', получен '{tok.value}'",
                position=tok.position,
            )
        return self._advance()

    def _match(self, *types: TokenType) -> bool:
        return self._current.type in types

    # ---- Grammar rules -----------------------------------------------------

    def _expression(self) -> ExprNode:
        """expression = term (('+' | '-') term)*"""
        left = self._term()
        while self._match(TokenType.PLUS, TokenType.MINUS):
            op = self._advance().value
            right = self._term()
            left = BinaryOpNode(op=op, left=left, right=right)
        return left

    def _term(self) -> ExprNode:
        """term = factor (('*' | '/') factor)*"""
        left = self._factor()
        while self._match(TokenType.STAR, TokenType.SLASH):
            op = self._advance().value
            right = self._factor()
            left = BinaryOpNode(op=op, left=left, right=right)
        return left

    def _factor(self) -> ExprNode:
        """factor = NUMBER | VARIABLE | FUNCTION '(' args ')' | '(' expr ')' | '-' factor"""
        tok = self._current

        # Unary minus
        if tok.type == TokenType.MINUS:
            self._advance()
            operand = self._factor()
            return UnaryOpNode(op="-", operand=operand)

        # Number
        if tok.type == TokenType.NUMBER:
            self._advance()
            return NumberNode(value=Decimal(tok.value))

        # Variable
        if tok.type == TokenType.VARIABLE:
            self._advance()
            return VariableNode(name=tok.value)

        # Function call
        if tok.type == TokenType.FUNCTION:
            name = tok.value
            self._advance()
            self._expect(TokenType.LPAREN)

            args: list[ExprNode] = []
            if not self._match(TokenType.RPAREN):
                args.append(self._expression())
                while self._match(TokenType.COMMA):
                    self._advance()
                    args.append(self._expression())

            self._expect(TokenType.RPAREN)
            return FunctionNode(name=name, args=args)

        # Parenthesized expression
        if tok.type == TokenType.LPAREN:
            self._advance()
            node = self._expression()
            self._expect(TokenType.RPAREN)
            return node

        raise FormulaSyntaxError(
            f"Неожиданный токен: '{tok.value}' ({tok.type.value})",
            position=tok.position,
        )


def parse_formula(source: str) -> ExprNode:
    """Convenience: parse a formula string into an AST."""
    return Parser(source).parse()
