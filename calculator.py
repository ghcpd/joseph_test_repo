"""
GUI Python Calculator (Tkinter)
BUG INJECTED: DO NOT FIX
Features: +, -, *, /, parentheses, decimal numbers, history
"""

import tkinter as tk

history = []  # stores last 5 calculations

def tokenize(expr):
    """Split expression into numbers, operators, and parentheses"""
    import re
    tokens = re.findall(r'\d+\.\d+|\d+|[()+\-*/]', expr)
    return tokens

def apply_operator(a, b, op):
    a = float(a)
    b = float(b)
    if op == '+':
        return a + b  # BUG: floating point precision bug
    elif op == '-':
        return a - b
    elif op == '*':
        return a * b
    elif op == '/':
        return a / b  # BUG: division by zero not handled
    else:
        raise ValueError("Unknown operator")

def evaluate(tokens):
    """Evaluate tokens without using eval()"""
    # BUG: operator precedence ignored, left-to-right evaluation
    stack = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token == '(':
            j = i + 1
            count = 1
            while j < len(tokens):
                if tokens[j] == '(':
                    count += 1
                elif tokens[j] == ')':
                    count -= 1
                if count == 0:
                    break
                j += 1
            if count != 0:
                return "Error: Mismatched parentheses"  # BUG: nested parentheses may fail
            val = evaluate(tokens[i+1:j])
            stack.append(val)
            i = j
        elif token in '+-*/':
            stack.append(token)
        else:
            stack.append(token)
        i += 1

    result = float(stack[0])
    idx = 1
    while idx < len(stack):
        op = stack[idx]
        next_val = float(stack[idx+1])
        result = apply_operator(result, next_val, op)
        idx += 2
    return result

def press(key):
    # BUG: repeated input bug not filtered
    entry.insert(tk.END, key)

def clear():
    global history
    entry.delete(0, tk.END)
    history = []  # BUG: clears history, not just current input
    update_history()

def calculate():
    global history
    expr = entry.get()
    try:
        tokens = tokenize(expr)
        result = evaluate(tokens)
        entry.delete(0, tk.END)
        entry.insert(0, str(result))
        # update history
        if len(history) < 5:
            history.append((expr, result))
        else:
            # BUG: overwrites oldest incorrectly
            history[0] = (expr, result)
        update_history()
    except Exception as e:
        entry.delete(0, tk.END)
        entry.insert(0, "Error")

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