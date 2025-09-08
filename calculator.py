#!/usr/bin/env python3

import argparse
import tkinter as tk
from tkinter import ttk


def safe_eval(expr: str) -> float:
    # Very minimal safe evaluator for +, -, *, /
    # Avoids using eval directly; relies on Python's eval with restricted globals
    allowed_chars = set("0123456789+-*/(). ")
    if not set(expr) <= allowed_chars:
        raise ValueError("Invalid characters in expression")
    # Evaluate with no builtins and empty globals/locals
    return eval(expr, {"__builtins__": {}}, {})


class Calculator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Python Calculator")
        self.resizable(False, False)
        self._build_ui()

    def _build_ui(self):
        self.display_var = tk.StringVar()
        entry = ttk.Entry(self, textvariable=self.display_var, justify="right", font=("Helvetica", 16))
        entry.grid(row=0, column=0, columnspan=4, padx=8, pady=8, sticky="nsew")

        buttons = [
            ('7', 1, 0), ('8', 1, 1), ('9', 1, 2), ('/', 1, 3),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('*', 2, 3),
            ('1', 3, 0), ('2', 3, 1), ('3', 3, 2), ('-', 3, 3),
            ('0', 4, 0), ('C', 4, 1), ('=', 4, 2), ('+', 4, 3),
        ]

        for (text, r, c) in buttons:
            action = (lambda t=text: self._on_button(t))
            btn = ttk.Button(self, text=text, command=action)
            btn.grid(row=r, column=c, padx=5, pady=5, sticky="nsew")

        for i in range(5):
            self.grid_rowconfigure(i, weight=1)
        for i in range(4):
            self.grid_columnconfigure(i, weight=1)

    def _on_button(self, char: str):
        if char == 'C':
            self.display_var.set('')
        elif char == '=':
            try:
                result = safe_eval(self.display_var.get())
                self.display_var.set(str(result))
            except Exception:
                self.display_var.set('Error')
        else:
            self.display_var.set(self.display_var.get() + char)


def main():
    parser = argparse.ArgumentParser(description="Simple Tkinter Calculator")
    parser.add_argument('--test', help='Evaluate expression in test mode without showing GUI')
    args = parser.parse_args()

    if args.test is not None:
        try:
            print(safe_eval(args.test))
        except Exception as e:
            print(f"Error: {e}")
        return

    app = Calculator()
    app.mainloop()


if __name__ == '__main__':
    main()
