"""
GUI Python Calculator (Tkinter)
BUG INJECTED: DO NOT FIX
Features: +, -, *, /, parentheses, decimal numbers, history
"""

import tkinter as tk
from decimal import Decimal, getcontext

history = []  # stores last 5 calculations
last_key = None
last_was_result = False

def tokenize(expr):
    """Split expression into numbers, operators, and parentheses"""
    import re
    tokens = re.findall(r'\d+\.\d+|\d+|[()+\-*/]', expr)
    # Validate that all characters are accounted for (reject invalid sequences like 1..2)
    compact = expr.replace(' ', '')
    if ''.join(tokens) != compact:
        raise ValueError("Error: Invalid characters or number format")
    return tokens

def apply_operator(a, b, op):
    if op == '+':
        return a + b
    elif op == '-':
        return a - b
    elif op == '*':
        return a * b
    elif op == '/':
        if b == 0:
            raise ValueError("Error: Division by zero")
        return a / b
    else:
        raise ValueError("Unknown operator")

def evaluate(tokens):
    """Evaluate tokens using shunting-yard algorithm with Decimal arithmetic"""
    # Convert to Reverse Polish Notation (RPN)
    output = []
    ops = []
    precedence = {'u+': 3, 'u-': 3, '*': 2, '/': 2, '+': 1, '-': 1}
    last_was_op = True  # start allows unary at beginning

    for token in tokens:
        if token.isdigit() or ('.' in token):
            output.append(Decimal(token))
            last_was_op = False
        elif token in '+-':
            # Handle unary +/−
            op = 'u+' if token == '+' else 'u-'
            if last_was_op:
                while ops and ops[-1] != '(' and precedence.get(ops[-1], 0) >= precedence[op]:
                    output.append(ops.pop())
                ops.append(op)
            else:
                # binary
                while ops and ops[-1] != '(' and precedence.get(ops[-1], 0) >= precedence[token]:
                    output.append(ops.pop())
                ops.append(token)
                last_was_op = True
        elif token in '*/':
            while ops and ops[-1] != '(' and precedence.get(ops[-1], 0) >= precedence[token]:
                output.append(ops.pop())
            ops.append(token)
            last_was_op = True
        elif token == '(':
            ops.append(token)
            last_was_op = True
        elif token == ')':
            while ops and ops[-1] != '(':
                output.append(ops.pop())
            if not ops or ops[-1] != '(':
                raise ValueError("Error: Mismatched parentheses")
            ops.pop()  # remove '('
            last_was_op = False
        else:
            raise ValueError("Error: Unknown token")

    while ops:
        if ops[-1] == '(':
            raise ValueError("Error: Mismatched parentheses")
        output.append(ops.pop())

    # Evaluate RPN
    stack = []
    for token in output:
        if isinstance(token, Decimal):
            stack.append(token)
        elif token in ('+', '-', '*', '/'):
            if len(stack) < 2:
                raise ValueError("Error: Invalid expression")
            b = stack.pop()
            a = stack.pop()
            stack.append(apply_operator(a, b, token))
        elif token in ('u+', 'u-'):
            if not stack:
                raise ValueError("Error: Invalid expression")
            a = stack.pop()
            stack.append(+a if token == 'u+' else -a)
        else:
            raise ValueError("Error: Invalid RPN token")

    if len(stack) != 1:
        raise ValueError("Error: Invalid expression")
    return stack[0]

def press(key):
    global last_key, last_was_result
    if last_was_result and key in '0123456789.(':
        entry.delete(0, tk.END)
        last_was_result = False
    # Debounce repeated digit inputs
    if key.isdigit() and last_key == key:
        return
    # Prevent multiple decimals in the current number
    if key == '.':
        current = entry.get()
        if not current or current[-1] in '+-*/(':
            entry.insert(tk.END, '0')
        # find last operator
        i = len(current) - 1
        while i >= 0 and current[i] not in '+-*/()':
            i -= 1
        segment = current[i+1:]
        if '.' in segment:
            return
    entry.insert(tk.END, key)
    last_key = key

def clear():
    entry.delete(0, tk.END)

def calculate():
    global history, last_was_result, last_key
    expr = entry.get()
    try:
        tokens = tokenize(expr)
        result = evaluate(tokens)
        # Format result: strip trailing zeros where appropriate
        result_str = str(result.normalize()) if result == result.normalize() else str(result)
        if '.' in result_str:
            # Ensure no exponent form
            result_str = format(result, 'f').rstrip('0').rstrip('.') or '0'
        entry.delete(0, tk.END)
        entry.insert(0, result_str)
        # update history FIFO size 5
        history.append((expr, result_str))
        if len(history) > 5:
            history.pop(0)
        update_history()
        last_was_result = True
        last_key = None
    except Exception as e:
        msg = str(e)
        entry.delete(0, tk.END)
        entry.insert(0, msg if msg.startswith("Error:") else "Error")
        last_was_result = False
        last_key = None

def update_history():
    if 'hist_text' not in globals() or hist_text is None:
        return
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