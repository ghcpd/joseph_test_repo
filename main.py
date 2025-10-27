#!/usr/bin/env python3
"""
Scientific Calculator Desktop Application

A graphical scientific calculator built with Python and Tkinter.
Supports basic arithmetic, scientific functions, memory operations,
and maintains a calculation history.

Author: GitHub Copilot Assistant
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# Add the current directory to the Python path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from ui import create_calculator
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure all required files (ui.py, calculator.py, parser.py) are present.")
    sys.exit(1)


def main():
    """Main entry point for the scientific calculator application."""
    try:
        # Create the calculator application
        root, app = create_calculator()
        
        # Set up the application icon and properties
        root.title("Scientific Calculator")
        
        # Handle application closing
        def on_closing():
            """Handle application closing."""
            if messagebox.askokcancel("Quit", "Do you want to quit the calculator?"):
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Center the window on screen
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Start the application
        print("Starting Scientific Calculator...")
        print("Features:")
        print("- Basic arithmetic operations (+, -, *, /)")
        print("- Scientific functions (sin, cos, tan, log, ln, sqrt, ^)")
        print("- Memory functions (MC, MR, M+, M-)")
        print("- Calculation history")
        print("- Keyboard input support")
        print("- Error handling")
        print("\nKeyboard shortcuts:")
        print("- Numbers and operators: Type directly")
        print("- Enter: Calculate")
        print("- Backspace: Delete last character")
        print("- Delete: Clear entry")
        print("- Escape: Clear all")
        print("- s: sin, c: cos, t: tan, l: log, n: ln, r: sqrt")
        
        root.mainloop()
        
    except Exception as e:
        error_msg = f"Failed to start calculator: {e}"
        print(error_msg)
        try:
            messagebox.showerror("Calculator Error", error_msg)
        except:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()