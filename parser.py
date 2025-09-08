import math
from typing import List, Union, Tuple

# Token types
NUMBER = 'NUMBER'
OPERATOR = 'OPERATOR'
LPAREN = 'LPAREN'
RPAREN = 'RPAREN'
FUNCTION = 'FUNCTION'
COMMA = 'COMMA'

# Operator precedence and associativity
OPERATORS = {
    '+': (2, 'L'),
    '-': (2, 'L'),
    '*': (3, 'L'),
    '/': (3, 'L'),
    '^': (4, 'R'),
}

FUNCTIONS = {
    'sin': 1,
    'cos': 1,
    'tan': 1,
    'log': 1,  # base 10
    'ln': 1,   # natural log
    'sqrt': 1,
}

class ParseError(Exception):
    """Exception for parse errors."""


def tokenize(expression: str) -> List[Tuple[str, Union[str, float]]]:
    """Converts the expression string into a list of tokens.

    Args:
        expression: The mathematical expression as a string.

    Returns:
        A list of tokens represented as tuples of (type, value).
    """
    tokens: List[Tuple[str, Union[str, float]]] = []
    i = 0
    n = len(expression)

    def is_function_start(ch: str) -> bool:
        return ch.isalpha()

    while i < n:
        ch = expression[i]
        if ch.isspace():
            i += 1
            continue
        if ch.isdigit() or ch == '.':
            # Parse number (including floats)
            start = i
            dot_seen = ch == '.'
            i += 1
            while i < n and (expression[i].isdigit() or (expression[i] == '.' and not dot_seen)):
                if expression[i] == '.':
                    dot_seen = True
                i += 1
            num_str = expression[start:i]
            try:
                num = float(num_str)
            except ValueError as e:
                raise ParseError(f"Invalid number '{num_str}'") from e
            tokens.append((NUMBER, num))
            continue
        if is_function_start(ch):
            # Parse function name
            start = i
            i += 1
            while i < n and expression[i].isalpha():
                i += 1
            name = expression[start:i]
            if name not in FUNCTIONS:
                raise ParseError(f"Unknown function '{name}'")
            tokens.append((FUNCTION, name))
            continue
        if ch in OPERATORS:
            # Determine unary minus
            if ch == '-':
                # If at start or previous token is operator, left paren, or comma, treat as unary
                if not tokens or tokens[-1][0] in (OPERATOR, LPAREN, COMMA, FUNCTION):
                    # Represent unary minus as a function 'neg'
                    tokens.append((FUNCTION, 'neg'))
                    i += 1
                    continue
            tokens.append((OPERATOR, ch))
            i += 1
            continue
        if ch == '(':
            tokens.append((LPAREN, ch))
            i += 1
            continue
        if ch == ')':
            tokens.append((RPAREN, ch))
            i += 1
            continue
        if ch == ',':
            tokens.append((COMMA, ch))
            i += 1
            continue
        raise ParseError(f"Unexpected character '{ch}' at position {i}")

    return tokens


def shunting_yard(tokens: List[Tuple[str, Union[str, float]]]) -> List[Tuple[str, Union[str, float]]]:
    """Convert tokens from infix notation to Reverse Polish Notation (RPN) using the shunting-yard algorithm."""
    output: List[Tuple[str, Union[str, float]]] = []
    stack: List[Tuple[str, Union[str, float]]] = []

    for tok_type, tok_val in tokens:
        if tok_type == NUMBER:
            output.append((NUMBER, tok_val))
        elif tok_type == FUNCTION:
            output.append((FUNCTION, tok_val)) if tok_val == 'neg' else stack.append((FUNCTION, tok_val))
        elif tok_type == COMMA:
            while stack and stack[-1][0] != LPAREN:
                output.append(stack.pop())
            if not stack:
                raise ParseError("Misplaced comma or mismatched parentheses")
        elif tok_type == OPERATOR:
            while stack:
                top_type, top_val = stack[-1]
                if top_type == OPERATOR:
                    p1, assoc1 = OPERATORS[tok_val]
                    p2, _ = OPERATORS[top_val]
                    if (assoc1 == 'L' and p1 <= p2) or (assoc1 == 'R' and p1 < p2):
                        output.append(stack.pop())
                    else:
                        break
                elif top_type in (FUNCTION,):
                    output.append(stack.pop())
                else:
                    break
            stack.append((OPERATOR, tok_val))
        elif tok_type == LPAREN:
            stack.append((LPAREN, tok_val))
        elif tok_type == RPAREN:
            while stack and stack[-1][0] != LPAREN:
                output.append(stack.pop())
            if not stack:
                raise ParseError("Mismatched parentheses")
            stack.pop()  # Pop the left parenthesis
            # If top of stack is a function, pop it too
            if stack and stack[-1][0] == FUNCTION:
                output.append(stack.pop())
        else:
            raise ParseError("Unknown token type")

    while stack:
        ttype, _ = stack[-1]
        if ttype in (LPAREN, RPAREN):
            raise ParseError("Mismatched parentheses")
        output.append(stack.pop())

    return output


def evaluate_rpn(rpn: List[Tuple[str, Union[str, float]]]) -> float:
    """Evaluate an expression in Reverse Polish Notation (RPN)."""
    stack: List[float] = []

    def apply_function(name: str, args: List[float]) -> float:
        if name == 'neg':
            if len(args) != 1:
                raise ValueError("neg expects 1 argument")
            return -args[0]
        if name == 'sin':
            return math.sin(args[0])
        if name == 'cos':
            return math.cos(args[0])
        if name == 'tan':
            return math.tan(args[0])
        if name == 'log':
            if args[0] <= 0:
                raise ValueError("log domain error")
            return math.log10(args[0])
        if name == 'ln':
            if args[0] <= 0:
                raise ValueError("ln domain error")
            return math.log(args[0])
        if name == 'sqrt':
            if args[0] < 0:
                raise ValueError("sqrt domain error")
            return math.sqrt(args[0])
        raise ValueError(f"Unknown function '{name}'")

    for tok_type, tok_val in rpn:
        if tok_type == NUMBER:
            stack.append(float(tok_val))
        elif tok_type == FUNCTION:
            if tok_val == 'neg':
                if not stack:
                    raise ValueError("Missing operand for negation")
                val = stack.pop()
                stack.append(apply_function('neg', [val]))
            else:
                if not stack:
                    raise ValueError(f"Missing operand for function '{tok_val}'")
                val = stack.pop()
                stack.append(apply_function(str(tok_val), [val]))
        elif tok_type == OPERATOR:
            if len(stack) < 2:
                raise ValueError("Insufficient operands")
            b = stack.pop()
            a = stack.pop()
            if tok_val == '+':
                stack.append(a + b)
            elif tok_val == '-':
                stack.append(a - b)
            elif tok_val == '*':
                stack.append(a * b)
            elif tok_val == '/':
                if b == 0:
                    raise ZeroDivisionError("Division by zero")
                stack.append(a / b)
            elif tok_val == '^':
                stack.append(a ** b)
            else:
                raise ValueError(f"Unknown operator '{tok_val}'")
        else:
            raise ValueError("Unknown token type in RPN")

    if len(stack) != 1:
        raise ValueError("Malformed expression")

    return stack[0]


def evaluate_expression(expr: str) -> float:
    """Evaluate a mathematical expression without using eval.

    Args:
        expr: The expression string to evaluate.

    Returns:
        The evaluated floating-point result.

    Raises:
        ParseError: If the expression cannot be parsed.
        ValueError/ZeroDivisionError: For evaluation errors.
    """
    tokens = tokenize(expr)
    rpn = shunting_yard(tokens)
    return evaluate_rpn(rpn)
