#!/usr/bin/env python3
import os
import sys
import tkinter as tk
from tkinter import ttk

# Attempt optional screenshot capability without adding hard dependencies
# Tries pyscreenshot first (works on many Linux environments), then PIL.ImageGrab

def try_save_screenshot(root, path="calculator_screenshot.png"):
    try:
        # Ensure window is up to date and visible
        root.update_idletasks()
        root.update()

        x = root.winfo_rootx()
        y = root.winfo_rooty()
        w = root.winfo_width()
        h = root.winfo_height()
        bbox = (x, y, x + w, y + h)

        try:
            import pyscreenshot as ImageGrab  # type: ignore
            img = ImageGrab.grab(bbox=bbox)
            img.save(path)
            print(f"Saved screenshot to {path}")
            return True
        except Exception:
            pass

        try:
            from PIL import ImageGrab  # type: ignore
            img = ImageGrab.grab(bbox=bbox)
            img.save(path)
            print(f"Saved screenshot to {path}")
            return True
        except Exception:
            pass
    except Exception:
        pass

    print("Unable to capture screenshot (optional).")
    return False


class Calculator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Calculator")
        self.resizable(False, False)

        # Display
        self.display_var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.display_var, justify="right", font=("Arial", 18))
        self.entry.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=8, pady=(8, 4))
        self.entry.focus_set()

        # Buttons layout
        buttons = [
            ["7", "8", "9", "÷"],
            ["4", "5", "6", "×"],
            ["1", "2", "3", "-"],
            ["C", "0", "=", "+"],
        ]

        for r, row in enumerate(buttons, start=1):
            for c, char in enumerate(row):
                btn = ttk.Button(self, text=char, command=lambda ch=char: self.on_button(ch))
                btn.grid(row=r, column=c, sticky="nsew", padx=4, pady=4, ipadx=4, ipady=6)

        for i in range(4):
            self.grid_columnconfigure(i, weight=1)
        for i in range(5):
            self.grid_rowconfigure(i, weight=1)

        # Key bindings
        self.bind("<Return>", lambda e: self.on_button("="))
        self.bind("<KP_Enter>", lambda e: self.on_button("="))
        for key in "0123456789+-*/":
            self.bind(key, self._key_insert)
        self.bind("c", lambda e: self.on_button("C"))
        self.bind("C", lambda e: self.on_button("C"))

    def _key_insert(self, event):
        mapping = {"*": "×", "/": "÷"}
        ch = mapping.get(event.char, event.char)
        self.display_var.set(self.display_var.get() + ch)

    def on_button(self, ch: str):
        if ch == "C":
            self.display_var.set("")
            return
        if ch == "=":
            expr = self.display_var.get().replace("×", "*").replace("÷", "/")
            try:
                # Evaluate using Python's eval with restricted globals and locals
                result = eval(expr, {"__builtins__": {}}, {})
                self.display_var.set(str(result))
            except Exception:
                self.display_var.set("Error")
            return
        self.display_var.set(self.display_var.get() + ch)


def main(argv=None):
    argv = argv or sys.argv[1:]
    app = Calculator()

    if "--screenshot" in argv or os.environ.get("CALC_SCREENSHOT"):
        # Place window then try to capture
        app.update()
        try_save_screenshot(app)
        app.destroy()
        return 0

    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
