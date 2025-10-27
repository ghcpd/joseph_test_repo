"""Expression parser using shunting-yard algorithm without eval.
Supports +, -, *, /, ^, parentheses, unary minus, and functions: sin, cos, tan, log, ln, sqrt.
"""
import math
from typing import List, Union

Number = float

FUNCTIONS = {
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'log': math.log10,
    'ln': math.log,
    'sqrt': math.sqrt,
}

OPERATORS = {
    '+': (1, 'left'),
    '-': (1, 'left'),
    '*': (2, 'left'),
    '/': (2, 'left'),
    '^': (5, 'right'),
    'u-': (4, 'right'),  # unary minus
}


def tokenize(expr: str) -> List[str]:
    tokens: List[str] = []
    i = 0
    while i < len(expr):
        c = expr[i]
        if c.isspace():
            i += 1
            continue
        if c.isdigit() or (c == '.' and i + 1 < len(expr) and expr[i+1].isdigit()):
            j = i + 1
            while j < len(expr) and (expr[j].isdigit() or expr[j] == '.'):
                j += 1
            tokens.append(expr[i:j])
            i = j
            continue
        if c.isalpha():
            j = i + 1
            while j < len(expr) and expr[j].isalpha():
                j += 1
            tokens.append(expr[i:j])
            i = j
            continue
        if c in '+-*/^(),':
            tokens.append(c)
            i += 1
            continue
        raise ValueError(f"Invalid character: {c}")
    # convert binary minus to unary when appropriate
    processed: List[str] = []
    prev: Union[str, None] = None
    for t in tokens:
        if t == '-' and (prev is None or prev in OPERATORS or prev in ('(', ',')):
            processed.append('u-')
        else:
            processed.append(t)
        prev = t
    return processed


def to_rpn(tokens: List[str]) -> List[str]:
    output: List[str] = []
    stack: List[str] = []
    for t in tokens:
        if t.replace('.', '', 1).isdigit():
            output.append(t)
        elif t in FUNCTIONS:
            stack.append(t)
        elif t in OPERATORS:
            p1, assoc1 = OPERATORS[t]
            while stack and stack[-1] in OPERATORS:
                p2, assoc2 = OPERATORS[stack[-1]]
                if (assoc1 == 'left' and p1 <= p2) or (assoc1 == 'right' and p1 < p2):
                    output.append(stack.pop())
                else:
                    break
            stack.append(t)
        elif t == '(':
            stack.append(t)
        elif t == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            if not stack:
                raise ValueError('Mismatched parentheses')
            stack.pop()  # pop '('
            if stack and stack[-1] in FUNCTIONS:
                output.append(stack.pop())
        else:
            raise ValueError(f'Unknown token: {t}')
    while stack:
        top = stack.pop()
        if top in ('(', ')'):
            raise ValueError('Mismatched parentheses')
        output.append(top)
    return output


def eval_rpn(rpn: List[str]) -> Number:
    st: List[Number] = []
    for t in rpn:
        if t.replace('.', '', 1).isdigit():
            st.append(float(t))
        elif t in FUNCTIONS:
            if not st:
                raise ValueError('Missing argument for function')
            x = st.pop()
            st.append(FUNCTIONS[t](x))
        elif t in OPERATORS:
            if t == 'u-':
                if not st:
                    raise ValueError('Missing operand for unary minus')
                st.append(-st.pop())
                continue
            if len(st) < 2:
                raise ValueError('Missing operands')
            b = st.pop(); a = st.pop()
            if t == '+': st.append(a + b)
            elif t == '-': st.append(a - b)
            elif t == '*': st.append(a * b)
            elif t == '/': st.append(a / b)
            elif t == '^': st.append(a ** b)
        else:
            raise ValueError(f'Unknown RPN token: {t}')
    if len(st) != 1:
        raise ValueError('Malformed expression')
    return st[0]


def evaluate(expr: str) -> Number:
    tokens = tokenize(expr)
    rpn = to_rpn(tokens)
    return eval_rpn(rpn)
