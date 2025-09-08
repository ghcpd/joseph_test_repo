"""
User Interface Module

This module provides the Tkinter-based graphical user interface for the
scientific calculator.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
from typing import Callable, Optional
from calculator import Calculator


class CalculatorUI:
    """
    Main UI class for the scientific calculator.
    """
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.calculator = Calculator()
        self.current_input = tk.StringVar(value="0")
        self.result_display = tk.StringVar(value="0")
        self.memory_indicator = tk.StringVar(value="")
        
        # Track if we just performed a calculation
        self.just_calculated = False
        
        self._setup_ui()
        self._setup_keyboard_bindings()
    
    def _setup_ui(self):
        """Set up the user interface."""
        self.root.title("Scientific Calculator")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # Configure grid weights for responsive design
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=3)
        main_frame.grid_columnconfigure(1, weight=1)
        
        # Create calculator frame (left side)
        calc_frame = ttk.Frame(main_frame)
        calc_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 10))
        
        # Create history frame (right side)
        history_frame = ttk.LabelFrame(main_frame, text="History", padding="5")
        history_frame.grid(row=0, column=1, rowspan=2, sticky="nsew")
        
        self._create_display(calc_frame)
        self._create_buttons(calc_frame)
        self._create_history_panel(history_frame)
    
    def _create_display(self, parent):
        """Create the display area."""
        display_frame = ttk.Frame(parent)
        display_frame.grid(row=0, column=0, columnspan=6, sticky="ew", pady=(0, 10))
        display_frame.grid_columnconfigure(0, weight=1)
        
        # Memory indicator
        memory_label = ttk.Label(display_frame, textvariable=self.memory_indicator,
                                font=("Arial", 10))
        memory_label.grid(row=0, column=0, sticky="w")
        
        # Input display (shows current expression being typed)
        input_frame = ttk.Frame(display_frame, relief="sunken", borderwidth=2)
        input_frame.grid(row=1, column=0, sticky="ew", pady=(5, 2))
        input_frame.grid_columnconfigure(0, weight=1)
        
        input_label = ttk.Label(input_frame, textvariable=self.current_input,
                               font=("Arial", 12), anchor="e", padding="5")
        input_label.grid(row=0, column=0, sticky="ew")
        
        # Result display (shows calculation result)
        result_frame = ttk.Frame(display_frame, relief="sunken", borderwidth=2)
        result_frame.grid(row=2, column=0, sticky="ew", pady=(2, 0))
        result_frame.grid_columnconfigure(0, weight=1)
        
        result_label = ttk.Label(result_frame, textvariable=self.result_display,
                                font=("Arial", 16, "bold"), anchor="e", padding="8")
        result_label.grid(row=0, column=0, sticky="ew")
    
    def _create_buttons(self, parent):
        """Create the calculator buttons."""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=1, column=0, sticky="nsew")
        
        # Configure grid weights
        for i in range(6):
            button_frame.grid_columnconfigure(i, weight=1)
        for i in range(8):
            button_frame.grid_rowconfigure(i, weight=1)
        
        # Button definitions (text, row, col, colspan, command, style)
        buttons = [
            # Row 0: Memory and clear functions
            ("MC", 0, 0, 1, self._memory_clear, "Memory.TButton"),
            ("MR", 0, 1, 1, self._memory_recall, "Memory.TButton"),
            ("M+", 0, 2, 1, self._memory_add, "Memory.TButton"),
            ("M-", 0, 3, 1, self._memory_subtract, "Memory.TButton"),
            ("C", 0, 4, 1, self._clear, "Clear.TButton"),
            ("CE", 0, 5, 1, self._clear_entry, "Clear.TButton"),
            
            # Row 1: Scientific functions
            ("sin", 1, 0, 1, lambda: self._append_function("sin"), "Function.TButton"),
            ("cos", 1, 1, 1, lambda: self._append_function("cos"), "Function.TButton"),
            ("tan", 1, 2, 1, lambda: self._append_function("tan"), "Function.TButton"),
            ("log", 1, 3, 1, lambda: self._append_function("log"), "Function.TButton"),
            ("ln", 1, 4, 1, lambda: self._append_function("ln"), "Function.TButton"),
            ("√", 1, 5, 1, lambda: self._append_function("sqrt"), "Function.TButton"),
            
            # Row 2: More functions and operators
            ("(", 2, 0, 1, lambda: self._append_text("("), "Operator.TButton"),
            (")", 2, 1, 1, lambda: self._append_text(")"), "Operator.TButton"),
            ("^", 2, 2, 1, lambda: self._append_text("^"), "Operator.TButton"),
            ("÷", 2, 3, 1, lambda: self._append_text("/"), "Operator.TButton"),
            ("×", 2, 4, 1, lambda: self._append_text("*"), "Operator.TButton"),
            ("←", 2, 5, 1, self._backspace, "Clear.TButton"),
            
            # Row 3-6: Number pad and basic operations
            ("7", 3, 0, 1, lambda: self._append_text("7"), "Number.TButton"),
            ("8", 3, 1, 1, lambda: self._append_text("8"), "Number.TButton"),
            ("9", 3, 2, 1, lambda: self._append_text("9"), "Number.TButton"),
            ("-", 3, 3, 1, lambda: self._append_text("-"), "Operator.TButton"),
            
            ("4", 4, 0, 1, lambda: self._append_text("4"), "Number.TButton"),
            ("5", 4, 1, 1, lambda: self._append_text("5"), "Number.TButton"),
            ("6", 4, 2, 1, lambda: self._append_text("6"), "Number.TButton"),
            ("+", 4, 3, 1, lambda: self._append_text("+"), "Operator.TButton"),
            
            ("1", 5, 0, 1, lambda: self._append_text("1"), "Number.TButton"),
            ("2", 5, 1, 1, lambda: self._append_text("2"), "Number.TButton"),
            ("3", 5, 2, 1, lambda: self._append_text("3"), "Number.TButton"),
            
            ("0", 6, 0, 2, lambda: self._append_text("0"), "Number.TButton"),
            (".", 6, 2, 1, lambda: self._append_text("."), "Number.TButton"),
            
            # Equals button spans multiple rows
            ("=", 3, 4, 1, self._calculate, "Equals.TButton"),
        ]
        
        # Create styles
        self._create_button_styles()
        
        # Create buttons
        for text, row, col, colspan, command, style in buttons:
            if text == "=" and row == 3:
                # Special case for equals button - make it span 4 rows
                btn = ttk.Button(button_frame, text=text, command=command, style=style)
                btn.grid(row=row, column=col, columnspan=colspan, rowspan=4, 
                        sticky="nsew", padx=2, pady=2)
            else:
                btn = ttk.Button(button_frame, text=text, command=command, style=style)
                btn.grid(row=row, column=col, columnspan=colspan, 
                        sticky="nsew", padx=2, pady=2)
    
    def _create_button_styles(self):
        """Create custom button styles."""
        style = ttk.Style()
        
        # Number buttons - light blue
        style.configure("Number.TButton", font=("Arial", 12), padding=5)
        
        # Operator buttons - orange
        style.configure("Operator.TButton", font=("Arial", 12), padding=5)
        
        # Function buttons - green
        style.configure("Function.TButton", font=("Arial", 10), padding=5)
        
        # Memory buttons - purple
        style.configure("Memory.TButton", font=("Arial", 10), padding=5)
        
        # Clear buttons - red
        style.configure("Clear.TButton", font=("Arial", 12), padding=5)
        
        # Equals button - dark blue
        style.configure("Equals.TButton", font=("Arial", 14, "bold"), padding=5)
    
    def _create_history_panel(self, parent):
        """Create the history panel."""
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        # History display
        self.history_text = scrolledtext.ScrolledText(
            parent, width=30, height=20, font=("Courier", 10),
            state="disabled", wrap=tk.WORD
        )
        self.history_text.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        
        # Clear history button
        clear_history_btn = ttk.Button(
            parent, text="Clear History", 
            command=self._clear_history
        )
        clear_history_btn.grid(row=1, column=0, sticky="ew")
        
        self._update_history_display()
    
    def _setup_keyboard_bindings(self):
        """Set up keyboard input support."""
        self.root.bind('<Key>', self._on_key_press)
        self.root.focus_set()
        
        # Make sure the window can receive focus
        self.root.bind('<Button-1>', lambda e: self.root.focus_set())
    
    def _on_key_press(self, event):
        """Handle keyboard input."""
        key = event.char
        keysym = event.keysym
        
        # Numbers and operators
        if key in "0123456789+-*/().":
            if key == "*":
                self._append_text("*")
            elif key == "/":
                self._append_text("/")
            else:
                self._append_text(key)
        
        # Special keys
        elif keysym == "Return" or keysym == "KP_Enter":
            self._calculate()
        elif keysym == "BackSpace":
            self._backspace()
        elif keysym == "Delete":
            self._clear_entry()
        elif keysym == "Escape":
            self._clear()
        elif key == "^":
            self._append_text("^")
        elif key == "s":
            self._append_function("sin")
        elif key == "c":
            self._append_function("cos")
        elif key == "t":
            self._append_function("tan")
        elif key == "l":
            self._append_function("log")
        elif key == "n":
            self._append_function("ln")
        elif key == "r":
            self._append_function("sqrt")
    
    def _append_text(self, text: str):
        """Append text to the current input."""
        current = self.current_input.get()
        
        # If we just calculated and user enters a number/operator, start fresh
        if self.just_calculated:
            if text in "0123456789.":
                current = ""
            elif text in "+-*/^":
                # Continue with the result for operators
                current = self.result_display.get()
            else:
                current = ""
            self.just_calculated = False
        
        # Handle initial "0"
        if current == "0" and text in "0123456789":
            current = ""
        
        self.current_input.set(current + text)
    
    def _append_function(self, func_name: str):
        """Append a function to the current input."""
        current = self.current_input.get()
        
        if self.just_calculated:
            current = ""
            self.just_calculated = False
        
        if current == "0":
            current = ""
        
        self.current_input.set(current + func_name + "(")
    
    def _backspace(self):
        """Remove the last character from input."""
        current = self.current_input.get()
        if len(current) > 1:
            self.current_input.set(current[:-1])
        else:
            self.current_input.set("0")
        self.just_calculated = False
    
    def _clear_entry(self):
        """Clear the current entry."""
        self.current_input.set("0")
        self.just_calculated = False
    
    def _clear(self):
        """Clear everything."""
        self.current_input.set("0")
        self.result_display.set("0")
        self.just_calculated = False
    
    def _calculate(self):
        """Perform the calculation."""
        expression = self.current_input.get()
        if expression == "0" or not expression.strip():
            return
        
        result = self.calculator.calculate(expression)
        self.result_display.set(result)
        self.just_calculated = True
        
        self._update_history_display()
        self._update_memory_indicator()
    
    def _memory_clear(self):
        """Clear memory."""
        self.calculator.memory_clear()
        self._update_memory_indicator()
    
    def _memory_recall(self):
        """Recall from memory."""
        memory_value = self.calculator.memory_recall()
        self.current_input.set(memory_value)
        self.just_calculated = False
    
    def _memory_add(self):
        """Add current result to memory."""
        current_result = self.result_display.get()
        if current_result and not current_result.startswith("Error"):
            self.calculator.memory_add(current_result)
            self._update_memory_indicator()
    
    def _memory_subtract(self):
        """Subtract current result from memory."""
        current_result = self.result_display.get()
        if current_result and not current_result.startswith("Error"):
            self.calculator.memory_subtract(current_result)
            self._update_memory_indicator()
    
    def _update_memory_indicator(self):
        """Update the memory indicator display."""
        if self.calculator.has_memory():
            self.memory_indicator.set("M")
        else:
            self.memory_indicator.set("")
    
    def _update_history_display(self):
        """Update the history display."""
        self.history_text.config(state="normal")
        self.history_text.delete(1.0, tk.END)
        
        history = self.calculator.get_history()
        if history:
            for expr, result, timestamp in reversed(history):  # Show newest first
                self.history_text.insert(tk.END, f"{timestamp}\n")
                self.history_text.insert(tk.END, f"{expr}\n")
                self.history_text.insert(tk.END, f"= {result}\n\n")
        else:
            self.history_text.insert(tk.END, "No calculations yet...")
        
        self.history_text.config(state="disabled")
        self.history_text.see(tk.END)
    
    def _clear_history(self):
        """Clear the calculation history."""
        self.calculator.clear_history()
        self._update_history_display()


def create_calculator():
    """Create and run the calculator application."""
    root = tk.Tk()
    app = CalculatorUI(root)
    return root, app


if __name__ == "__main__":
    root, app = create_calculator()
    root.mainloop()