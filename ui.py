import tkinter as tk
from tkinter import messagebox
from typing import List
from calculator import Calculator

class CalculatorUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Scientific Calculator")
        self.calc = Calculator()

        self.entry = tk.Entry(root, width=30, font=("Arial", 18), justify='right')
        self.entry.grid(row=0, column=0, columnspan=6, padx=10, pady=10, sticky='nsew')

        # History panel
        self.history_list = tk.Listbox(root, height=10, width=40)
        self.history_list.grid(row=1, column=6, rowspan=6, padx=(10, 10), pady=10, sticky='nsew')

        buttons: List[List[str]] = [
            ['7', '8', '9', '/', 'sin', 'cos'],
            ['4', '5', '6', '*', 'tan', 'log'],
            ['1', '2', '3', '-', 'ln',  'sqrt'],
            ['0', '.', '(', ')', '^',   '='],
            ['MC', 'MR', 'M+', 'M-', 'C', '⌫'],
        ]

        for r, row in enumerate(buttons, start=1):
            for c, text in enumerate(row):
                action = (lambda t=text: self.on_button_click(t))
                tk.Button(root, text=text, width=6, height=2, command=action).grid(row=r, column=c, padx=5, pady=5, sticky='nsew')

        # Configure grid weights
        for i in range(7):
            root.grid_columnconfigure(i, weight=1)
        for i in range(1, 7):
            root.grid_rowconfigure(i, weight=1)

        # Keyboard bindings
        for ch in '0123456789.+-*/^()':
            root.bind(ch, self.on_key)
        root.bind('<Return>', lambda e: self.on_button_click('='))
        root.bind('<BackSpace>', lambda e: self.on_button_click('⌫'))
        root.bind('<Escape>', lambda e: self.on_button_click('C'))

    def on_key(self, event: tk.Event) -> None:
        self.entry.insert(tk.END, event.char)

    def on_button_click(self, text: str) -> None:
        if text == '=':
            expr = self.entry.get()
            result = self.calc.calculate(expr)
            if result.startswith('Error'):
                messagebox.showerror("Error", result)
            else:
                self.entry.delete(0, tk.END)
                self.entry.insert(0, result)
            self.update_history()
        elif text == 'C':
            self.entry.delete(0, tk.END)
        elif text == '⌫':
            current = self.entry.get()
            if current:
                self.entry.delete(len(current)-1, tk.END)
        elif text in ('MC', 'MR', 'M+', 'M-'):
            self.handle_memory(text)
        elif text in ('sin', 'cos', 'tan', 'log', 'ln', 'sqrt'):
            self.entry.insert(tk.END, f"{text}(")
        else:
            self.entry.insert(tk.END, text)

    def handle_memory(self, op: str) -> None:
        if op == 'MC':
            self.calc.memory_clear()
        elif op == 'MR':
            val = self.calc.memory_recall()
            self.entry.insert(tk.END, str(val))
        else:
            try:
                current = self.entry.get() or '0'
                value = float(self.calc.calculate(current))
                if op == 'M+':
                    self.calc.memory_add(value)
                elif op == 'M-':
                    self.calc.memory_subtract(value)
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def update_history(self) -> None:
        self.history_list.delete(0, tk.END)
        for expr, result in self.calc.history:
            self.history_list.insert(tk.END, f"{expr} = {result}")
