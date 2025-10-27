"""
Expression Parser Module

This module provides functionality to parse and evaluate mathematical expressions
without using Python's built-in eval() function. It supports basic arithmetic,
scientific functions, and parentheses with proper operator precedence.
"""

import re
import math
from typing import List, Union, Callable, Dict


class Token:
    """Represents a token in a mathematical expression."""
    
    def __init__(self, type_: str, value: str, position: int = 0):
        self.type = type_
        self.value = value
        self.position = position
    
    def __repr__(self):
        return f"Token({self.type}, {self.value})"


class ParseError(Exception):
    """Exception raised when parsing fails."""
    pass


class Tokenizer:
    """Tokenizes mathematical expressions into a list of tokens."""
    
    # Token patterns
    TOKEN_PATTERNS = [
        ('NUMBER', r'\d+\.?\d*'),           # Numbers (int or float)
        ('FUNCTION', r'[a-zA-Z]+'),         # Function names
        ('LPAREN', r'\('),                  # Left parenthesis
        ('RPAREN', r'\)'),                  # Right parenthesis
        ('POWER', r'\^'),                   # Exponentiation
        ('MULTIPLY', r'\*'),                # Multiplication
        ('DIVIDE', r'/'),                   # Division
        ('PLUS', r'\+'),                    # Addition
        ('MINUS', r'-'),                    # Subtraction
        ('WHITESPACE', r'\s+'),             # Whitespace (ignored)
    ]
    
    def __init__(self):
        # Compile patterns for efficiency
        self.compiled_patterns = [
            (name, re.compile(pattern))
            for name, pattern in self.TOKEN_PATTERNS
        ]
    
    def tokenize(self, expression: str) -> List[Token]:
        """
        Tokenize a mathematical expression into a list of tokens.
        
        Args:
            expression: The mathematical expression to tokenize
            
        Returns:
            List of Token objects
            
        Raises:
            ParseError: If invalid characters are found
        """
        tokens = []
        position = 0
        
        while position < len(expression):
            match_found = False
            
            for token_type, pattern in self.compiled_patterns:
                match = pattern.match(expression, position)
                if match:
                    value = match.group(0)
                    
                    # Skip whitespace tokens
                    if token_type != 'WHITESPACE':
                        tokens.append(Token(token_type, value, position))
                    
                    position = match.end()
                    match_found = True
                    break
            
            if not match_found:
                raise ParseError(f"Invalid character '{expression[position]}' at position {position}")
        
        return tokens


class ExpressionParser:
    """
    Recursive descent parser for mathematical expressions.
    
    Grammar:
    expression  := term (('+' | '-') term)*
    term        := factor (('*' | '/') factor)*
    factor      := power
    power       := atom ('^' atom)*
    atom        := NUMBER | FUNCTION '(' expression ')' | '(' expression ')' | '-' atom
    """
    
    # Supported mathematical functions
    FUNCTIONS: Dict[str, Callable[[float], float]] = {
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'log': math.log10,
        'ln': math.log,
        'sqrt': math.sqrt,
        'abs': abs,
    }
    
    def __init__(self):
        self.tokenizer = Tokenizer()
        self.tokens: List[Token] = []
        self.position = 0
    
    def parse(self, expression: str) -> float:
        """
        Parse and evaluate a mathematical expression.
        
        Args:
            expression: The mathematical expression to evaluate
            
        Returns:
            The numerical result of the expression
            
        Raises:
            ParseError: If the expression is malformed
            ZeroDivisionError: If division by zero occurs
            ValueError: If invalid function arguments are provided
        """
        self.tokens = self.tokenizer.tokenize(expression)
        self.position = 0
        
        if not self.tokens:
            raise ParseError("Empty expression")
        
        result = self._parse_expression()
        
        # Check if we've consumed all tokens
        if self.position < len(self.tokens):
            raise ParseError(f"Unexpected token: {self.tokens[self.position].value}")
        
        return result
    
    def _current_token(self) -> Union[Token, None]:
        """Get the current token without advancing position."""
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        return None
    
    def _consume_token(self, expected_type: str = None) -> Token:
        """
        Consume and return the current token.
        
        Args:
            expected_type: Optional type to check against
            
        Returns:
            The consumed token
            
        Raises:
            ParseError: If token type doesn't match expected or no more tokens
        """
        if self.position >= len(self.tokens):
            raise ParseError("Unexpected end of expression")
        
        token = self.tokens[self.position]
        
        if expected_type and token.type != expected_type:
            raise ParseError(f"Expected {expected_type}, got {token.type}")
        
        self.position += 1
        return token
    
    def _parse_expression(self) -> float:
        """Parse addition and subtraction (lowest precedence)."""
        result = self._parse_term()
        
        while self._current_token() and self._current_token().type in ('PLUS', 'MINUS'):
            operator = self._consume_token()
            right = self._parse_term()
            
            if operator.type == 'PLUS':
                result += right
            else:  # MINUS
                result -= right
        
        return result
    
    def _parse_term(self) -> float:
        """Parse multiplication and division."""
        result = self._parse_factor()
        
        while self._current_token() and self._current_token().type in ('MULTIPLY', 'DIVIDE'):
            operator = self._consume_token()
            right = self._parse_factor()
            
            if operator.type == 'MULTIPLY':
                result *= right
            else:  # DIVIDE
                if right == 0:
                    raise ZeroDivisionError("Division by zero")
                result /= right
        
        return result
    
    def _parse_factor(self) -> float:
        """Parse factors (handles unary minus)."""
        return self._parse_power()
    
    def _parse_power(self) -> float:
        """Parse exponentiation (right associative)."""
        result = self._parse_atom()
        
        if self._current_token() and self._current_token().type == 'POWER':
            self._consume_token('POWER')
            exponent = self._parse_power()  # Right associative
            result = math.pow(result, exponent)
        
        return result
    
    def _parse_atom(self) -> float:
        """Parse atomic values: numbers, functions, parentheses, unary minus."""
        token = self._current_token()
        
        if not token:
            raise ParseError("Unexpected end of expression")
        
        # Handle unary minus
        if token.type == 'MINUS':
            self._consume_token('MINUS')
            return -self._parse_atom()
        
        # Handle numbers
        elif token.type == 'NUMBER':
            token = self._consume_token('NUMBER')
            try:
                return float(token.value)
            except ValueError:
                raise ParseError(f"Invalid number: {token.value}")
        
        # Handle functions
        elif token.type == 'FUNCTION':
            function_token = self._consume_token('FUNCTION')
            function_name = function_token.value.lower()
            
            if function_name not in self.FUNCTIONS:
                raise ParseError(f"Unknown function: {function_name}")
            
            self._consume_token('LPAREN')
            argument = self._parse_expression()
            self._consume_token('RPAREN')
            
            try:
                return self.FUNCTIONS[function_name](argument)
            except (ValueError, OverflowError) as e:
                raise ParseError(f"Function error in {function_name}({argument}): {str(e)}")
        
        # Handle parentheses
        elif token.type == 'LPAREN':
            self._consume_token('LPAREN')
            result = self._parse_expression()
            self._consume_token('RPAREN')
            return result
        
        else:
            raise ParseError(f"Unexpected token: {token.value}")


def evaluate_expression(expression: str) -> float:
    """
    Convenience function to evaluate a mathematical expression.
    
    Args:
        expression: The mathematical expression to evaluate
        
    Returns:
        The numerical result
        
    Raises:
        ParseError: If the expression is malformed
        ZeroDivisionError: If division by zero occurs
        ValueError: If invalid function arguments are provided
    """
    parser = ExpressionParser()
    return parser.parse(expression)


if __name__ == "__main__":
    # Test the parser
    test_expressions = [
        "2 + 3 * 4",
        "(2 + 3) * 4",
        "sin(0)",
        "cos(0)",
        "sqrt(16)",
        "2^3",
        "log(100)",
        "ln(2.718)",
        "-5 + 3",
        "2 * -3",
    ]
    
    parser = ExpressionParser()
    
    for expr in test_expressions:
        try:
            result = parser.parse(expr)
            print(f"{expr} = {result}")
        except Exception as e:
            print(f"{expr} = ERROR: {e}")