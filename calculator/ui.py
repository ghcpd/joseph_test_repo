"""Tkinter UI for the scientific calculator."""
import tkinter as tk
from tkinter import messagebox
from typing import Callable
from .calculator import Calculator

class CalculatorUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title('Scientific Calculator')
        self.calc = Calculator()

        self.entry = tk.Entry(root, width=28, font=('Arial', 18))
        self.entry.grid(row=0, column=0, columnspan=6, padx=8, pady=8, sticky='nsew')

        self.history = tk.Listbox(root, height=10)
        self.history.grid(row=1, column=4, rowspan=6, padx=8, pady=8, sticky='nsew')

        buttons = [
            ('7', self._ins('7')), ('8', self._ins('8')), ('9', self._ins('9')), ('/', self._ins('/')),
            ('sin', self._ins('sin(')), ('cos', self._ins('cos(')),
            ('4', self._ins('4')), ('5', self._ins('5')), ('6', self._ins('6')), ('*', self._ins('*')),
            ('tan', self._ins('tan(')), ('log', self._ins('log(')),
            ('1', self._ins('1')), ('2', self._ins('2')), ('3', self._ins('3')), ('-', self._ins('-')),
            ('ln', self._ins('ln(')), ('sqrt', self._ins('sqrt(')),
            ('0', self._ins('0')), ('.', self._ins('.')), ('(', self._ins('(')), (')', self._ins(')')),
            ('^', self._ins('^')), ('+', self._ins('+')),
        ]

        r = 1; c = 0
        for text, cmd in buttons:
            b = tk.Button(root, text=text, width=5, command=cmd)
            b.grid(row=r, column=c, padx=2, pady=2, sticky='nsew')
            c += 1
            if c == 4:
                r += 1; c = 0

        # bottom row with equals and clear
        tk.Button(root, text='C', command=self.clear).grid(row=r, column=0, padx=2, pady=2, sticky='nsew')
        tk.Button(root, text='=', command=self.calculate).grid(row=r, column=1, padx=2, pady=2, sticky='nsew')
        tk.Button(root, text='M+', command=self.m_plus).grid(row=r, column=2, padx=2, pady=2, sticky='nsew')
        tk.Button(root, text='M-', command=self.m_minus).grid(row=r, column=3, padx=2, pady=2, sticky='nsew')
        tk.Button(root, text='MR', command=self.mr).grid(row=r, column=4, padx=2, pady=2, sticky='nsew')
        tk.Button(root, text='MC', command=self.mc).grid(row=r, column=5, padx=2, pady=2, sticky='nsew')

        # grid weights
        for i in range(6):
            root.grid_columnconfigure(i, weight=1)
        for i in range(r+1):
            root.grid_rowconfigure(i, weight=1)

        # keyboard support
        root.bind('<Return>', lambda e: self.calculate())

    def _ins(self, text: str) -> Callable[[], None]:
        def f() -> None:
            self.entry.insert(tk.END, text)
        return f

    def clear(self) -> None:
        self.entry.delete(0, tk.END)

    def calculate(self) -> None:
        expr = self.entry.get()
        result = self.calc.evaluate(expr)
        if result.startswith('Error:'):
            messagebox.showerror('Calculation Error', result)
        else:
            self.entry.delete(0, tk.END)
            self.entry.insert(0, result)
        self._refresh_history()

    def _refresh_history(self) -> None:
        self.history.delete(0, tk.END)
        for e, r in self.calc.history:
            self.history.insert(tk.END, f"{e} = {r}")

    # memory funcs
    def m_plus(self) -> None:
        try:
            val = float(self.entry.get())
        except Exception:
            return
        self.calc.memory_add(val)

    def m_minus(self) -> None:
        try:
            val = float(self.entry.get())
        except Exception:
            return
        self.calc.memory_subtract(val)

    def mr(self) -> None:
        self.entry.delete(0, tk.END)
        self.entry.insert(0, str(self.calc.memory_recall()))

    def mc(self) -> None:
        self.calc.memory_clear()


def main() -> None:
    root = tk.Tk()
    CalculatorUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
