"""
GUI Python Calculator (Tkinter)
Features: +, -, *, /, parentheses, decimal numbers, history
Fixed version addressing all identified bugs
"""

import tkinter as tk
from decimal import Decimal, InvalidOperation
import re
import time

history = []  # stores last 5 calculations
last_input_time = {}  # for debouncing
calculator_state = "input"  # "input" or "result"

def tokenize(expr):
    """Split expression into numbers, operators, and parentheses"""
    # Check for multiple decimal points in a number
    if re.search(r'\d+\.\d*\.\d*', expr):
        return ["ERROR_MULTIPLE_DECIMALS"]
    
    # Find all tokens
    tokens = re.findall(r'\d+\.\d+|\d+|[()+\-*/]', expr)
    
    # Validate consecutive operators - only +- and -- should be allowed
    for i in range(len(tokens) - 1):
        if tokens[i] in '+-*/' and tokens[i+1] in '+-*/':
            # Allow +-, --, +- combinations but not */ combinations
            if (tokens[i] in '*/' and tokens[i+1] in '+-') or \
               (tokens[i] in '*/' and tokens[i+1] in '*/') or \
               (tokens[i] in '+-' and tokens[i+1] in '*/'):
                return ["ERROR_INVALID_OPERATORS"]
    
    return tokens

def apply_operator(a, b, op):
    """Apply operator with proper precision and error handling"""
    try:
        # Use Decimal for precise floating point arithmetic
        a_dec = Decimal(str(a))
        b_dec = Decimal(str(b))
        
        if op == '+':
            result = a_dec + b_dec
        elif op == '-':
            result = a_dec - b_dec
        elif op == '*':
            result = a_dec * b_dec
        elif op == '/':
            if b_dec == 0:
                return "Error: Division by zero"
            result = a_dec / b_dec
        else:
            return "Error: Unknown operator"
        
        # Convert back to float, handling precision appropriately
        result_float = float(result)
        # Round to 10 decimal places to avoid floating point artifacts
        return round(result_float, 10)
        
    except (InvalidOperation, ValueError):
        return "Error: Invalid number"

def evaluate(tokens):
    """Evaluate tokens with proper operator precedence without using eval()"""
    
    # Check for error tokens first
    if any(token.startswith("ERROR_") for token in tokens):
        if "ERROR_MULTIPLE_DECIMALS" in tokens:
            return "Error: Multiple decimal points"
        if "ERROR_INVALID_OPERATORS" in tokens:
            return "Error: Invalid operator sequence"
    
    if not tokens:
        return "Error: Empty expression"
    
    try:
        return evaluate_expression(tokens)
    except Exception as e:
        if "division by zero" in str(e).lower():
            return "Error: Division by zero"
        return f"Error: {str(e)}"


def evaluate_expression(tokens):
    """Recursive descent parser for arithmetic expressions with proper precedence"""
    
    # Handle parentheses first
    while '(' in tokens:
        # Find innermost parentheses
        start = -1
        for i, token in enumerate(tokens):
            if token == '(':
                start = i
            elif token == ')':
                if start == -1:
                    raise ValueError("Mismatched parentheses")
                # Evaluate the expression inside parentheses
                inner_result = evaluate_expression(tokens[start+1:i])
                if isinstance(inner_result, str) and inner_result.startswith("Error"):
                    return inner_result
                # Replace the parentheses and contents with the result
                tokens = tokens[:start] + [str(inner_result)] + tokens[i+1:]
                break
        else:
            if start != -1:
                raise ValueError("Mismatched parentheses")
    
    # Handle leading negative sign
    if tokens and tokens[0] == '-':
        if len(tokens) < 2:
            raise ValueError("Invalid expression")
        tokens = [str(-float(tokens[1]))] + tokens[2:]
    
    # Handle single number case
    if len(tokens) == 1:
        try:
            return float(tokens[0])
        except ValueError:
            raise ValueError("Invalid number")
    
    # Now handle operator precedence: * and / first, then + and -
    # Convert consecutive +- or -- to single numbers
    i = 0
    while i < len(tokens) - 1:
        if tokens[i] in '+-' and tokens[i+1] in '+-':
            # Handle consecutive signs
            if i == 0:  # Leading sign
                if tokens[i] == '-':
                    tokens = [str(-float(tokens[i+1]))] + tokens[i+2:]
                else:
                    tokens = tokens[i+1:]  # Remove leading +
            else:
                # Combine signs: +- becomes -, -- becomes +, ++ becomes +, -+ becomes -
                prev_op = tokens[i-1] if i > 0 and tokens[i-1] in '+-*/' else '+'
                if tokens[i] == '+' and tokens[i+1] == '-':
                    tokens[i] = '-'
                    tokens.pop(i+1)
                elif tokens[i] == '-' and tokens[i+1] == '-':
                    tokens[i] = '+'
                    tokens.pop(i+1)
                elif tokens[i] == '-' and tokens[i+1] == '+':
                    tokens[i] = '-'
                    tokens.pop(i+1)
                elif tokens[i] == '+' and tokens[i+1] == '+':
                    tokens.pop(i+1)
                else:
                    i += 1
        else:
            i += 1
    
    # Handle multiplication and division first (higher precedence)
    i = 1
    while i < len(tokens):
        if i < len(tokens) and tokens[i] in '*/':
            if i == 0 or i >= len(tokens) - 1:
                raise ValueError("Invalid operator position")
            
            left = float(tokens[i-1])
            op = tokens[i]
            right = float(tokens[i+1])
            
            result = apply_operator(left, right, op)
            if isinstance(result, str) and result.startswith("Error"):
                return result
                
            # Replace the three tokens with the result
            tokens = tokens[:i-1] + [str(result)] + tokens[i+2:]
        else:
            i += 1
    
    # Handle addition and subtraction (lower precedence)
    i = 1
    while i < len(tokens):
        if i < len(tokens) and tokens[i] in '+-':
            if i == 0 or i >= len(tokens) - 1:
                raise ValueError("Invalid operator position")
                
            left = float(tokens[i-1])
            op = tokens[i]
            right = float(tokens[i+1])
            
            result = apply_operator(left, right, op)
            if isinstance(result, str) and result.startswith("Error"):
                return result
                
            # Replace the three tokens with the result
            tokens = tokens[:i-1] + [str(result)] + tokens[i+2:]
        else:
            i += 1
    
    if len(tokens) == 1:
        return float(tokens[0])
    else:
        raise ValueError("Invalid expression")

def press(key):
    """Handle button press with debouncing and state management"""
    global calculator_state, last_input_time
    
    current_time = time.time()
    
    # Debouncing: ignore rapid repeated presses of the same key
    if key in last_input_time and current_time - last_input_time[key] < 0.5:
        return  # Ignore rapid repeat
    
    last_input_time[key] = current_time
    
    # If we're in result state and user presses a number/operator, clear first
    if calculator_state == "result":
        if key in '0123456789.+-*/()':
            entry.delete(0, tk.END)
        calculator_state = "input"
    
    entry.insert(tk.END, key)

def clear():
    """Clear entry but preserve history"""
    global calculator_state
    if 'entry' in globals():  # Only clear if GUI is initialized
        entry.delete(0, tk.END)
    calculator_state = "input"
    if 'hist_text' in globals():
        update_history()

def calculate():
    """Calculate result and manage FIFO history"""
    global history, calculator_state
    
    if 'entry' not in globals():
        return  # No GUI initialized
        
    expr = entry.get()
    if not expr:
        return
        
    try:
        tokens = tokenize(expr)
        result = evaluate(tokens)
        
        # Handle errors
        if isinstance(result, str) and result.startswith("Error"):
            entry.delete(0, tk.END)
            entry.insert(0, result)
            calculator_state = "result"
            return
            
        # Display result
        entry.delete(0, tk.END)
        entry.insert(0, str(result))
        calculator_state = "result"
        
        # Update history with FIFO behavior (maximum 5 items)
        if len(history) >= 5:
            history.pop(0)  # Remove oldest entry
        history.append((expr, result))
        
        if 'hist_text' in globals():
            update_history()
            
    except Exception as e:
        entry.delete(0, tk.END)
        entry.insert(0, "Error")
        calculator_state = "result"

def update_history():
    """Update history display"""
    if 'hist_text' not in globals():
        return  # No GUI initialized
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