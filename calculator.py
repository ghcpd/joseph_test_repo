"""
GUI Python Calculator (Tkinter)
BUG INJECTED: DO NOT FIX
Features: +, -, *, /, parentheses, decimal numbers, history
"""

import tkinter as tk
from decimal import Decimal, DivisionByZero, InvalidOperation
last_was_result = False

history = []  # stores last 5 calculations

def tokenize(expr):
    """Split expression into numbers, operators, and parentheses"""
    import re
    tokens = re.findall(r'\d+\.\d+|\d+|[()+\-*/]', expr)
    return tokens

def apply_operator(a, b, op):
    a = Decimal(str(a))
    b = Decimal(str(b))
    if op == '+':
        return a + b
    elif op == '-':
        return a - b
    elif op == '*':
        return a * b
    elif op == '/':
        if b == 0:
            raise ZeroDivisionError('Division by zero')
        return a / b
    else:
        raise ValueError("Unknown operator")

def evaluate(tokens):
    """Evaluate tokens without using eval(), respecting operator precedence and parentheses.
    Supports unary + and -.
    """
    # Parser functions
    def parse_expression(i):
        val, i = parse_term(i)
        while i < len(tokens) and tokens[i] in ('+','-'):
            op = tokens[i]
            rhs, i = parse_term(i+1)
            val = apply_operator(val, rhs, op)
        return val, i

    def parse_term(i):
        val, i = parse_factor(i)
        while i < len(tokens) and tokens[i] in ('*','/'):
            op = tokens[i]
            rhs, i = parse_factor(i+1)
            val = apply_operator(val, rhs, op)
        return val, i

    def parse_factor(i):
        if i >= len(tokens):
            raise ValueError('Invalid expression')
        t = tokens[i]
        if t in ('+','-'):
            # unary
            val, j = parse_factor(i+1)
            if t == '-':
                return apply_operator(0, val, '-'), j
            else:
                return val, j
        if t == '(':
            val, j = parse_expression(i+1)
            if j >= len(tokens) or tokens[j] != ')':
                raise ValueError('Mismatched parentheses')
            return val, j+1
        # number
        if t == '.' or t in ('*','/'):  # invalid factor
            raise ValueError('Invalid expression')
        try:
            return Decimal(t), i+1
        except Exception:
            raise ValueError('Invalid number')

    val, idx = parse_expression(0)
    if idx != len(tokens):
        raise ValueError('Invalid expression')
    return val.normalize()

def press(key):
    global last_was_result
    text = ''
    try:
        text = entry.get()
    except Exception:
        text = ''
    if last_was_result:
        entry.delete(0, tk.END)
        text = ''
        last_was_result = False
    # debounce identical consecutive digits
    if key.isdigit() and text.endswith(key):
        return

    entry.insert(tk.END, key)

def clear():
    entry.delete(0, tk.END)

def calculate():
    global history, last_was_result
    expr = entry.get()
    try:
        tokens = tokenize(expr)
        result = evaluate(tokens)
        entry.delete(0, tk.END)
        entry.insert(0, str(result))
        last_was_result = True
        # update history FIFO (size 5)
        history.append((expr, result))
        if len(history) > 5:
            history.pop(0)
        update_history()
    except ZeroDivisionError:
        entry.delete(0, tk.END)
        entry.insert(0, "Error: Division by zero")
        last_was_result = False
    except Exception:
        entry.delete(0, tk.END)
        entry.insert(0, "Error: Invalid expression")
        last_was_result = False

def update_history():
    hist_text.delete('1.0', tk.END)
    for expr, res in history:
        hist_text.insert(tk.END, f"{expr} = {res}\n")

# GUI setup wrapped so tests can import without launching the window
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Buggy Calculator")

    entry = tk.Entry(root, width=25, font=('Arial', 16))
    entry.grid(row=0, column=0, columnspan=4)

    buttons = [
        '7','8','9','/',
        '4','5','6','*',
        '1','2','3','-',
        '0','.','+','(',
        ')','C','=',''
    ]

    row = 1
    col = 0
    for b in buttons:
        if b != '':
            action = (lambda x=b: press(x)) if b not in ['C','=',] else (clear if b=='C' else calculate)
            tk.Button(root, text=b, width=5, height=2, command=action).grid(row=row, column=col)
        col += 1
        if col > 3:
            col = 0
            row += 1

    hist_text = tk.Text(root, height=5, width=25)
    hist_text.grid(row=row, column=0, columnspan=4)

    root.mainloop()

"""
TEST EXPRESSIONS (may fail due to bugs):
1. 2+2 → expected 4
2. 0.1+0.2 → expected 0.3, may get 0.30000000000000004
3. 2+3*4 → expected 14, may get 20 (precedence bug)
4. 2*(3+4) → expected 14, may fail (parentheses bug)
5. 5/0 → may crash or return Infinity
6. 5+-3 → may crash (consecutive operator bug)
7. Rapid button clicks "1" may insert "11" (input repetition bug)
8. 1..2 → may crash or return NaN (multiple decimal points)
"""