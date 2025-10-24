#!/usr/bin/env python3
"""
Unit Converter GUI Application
A Tkinter-based GUI for converting between different units across multiple categories.
"""

import tkinter as tk
from tkinter import ttk, messagebox


class UnitConverter:
    """Main Unit Converter application class."""
    
    def __init__(self, root):
        """Initialize the Unit Converter GUI.
        
        Args:
            root: The main Tkinter window
        """
        self.root = root
        self.root.title("Unit Converter")
        self.root.geometry("600x300")
        self.root.resizable(False, False)
        
        # Define conversion data: category -> {unit: conversion_factor_to_base}
        # Base units: meter, liter, kilogram, celsius, second
        self.conversion_data = {
            "Length": {
                "Meter": 1.0,
                "Kilometer": 1000.0,
                "Centimeter": 0.01,
                "Millimeter": 0.001,
                "Mile": 1609.344,
                "Yard": 0.9144,
                "Foot": 0.3048,
                "Inch": 0.0254
            },
            "Volume": {
                "Liter": 1.0,
                "Milliliter": 0.001,
                "Gallon (US)": 3.78541,
                "Quart (US)": 0.946353,
                "Pint (US)": 0.473176,
                "Cup (US)": 0.236588,
                "Fluid Ounce (US)": 0.0295735,
                "Cubic Meter": 1000.0,
                "Cubic Centimeter": 0.001
            },
            "Weight": {
                "Kilogram": 1.0,
                "Gram": 0.001,
                "Milligram": 0.000001,
                "Metric Ton": 1000.0,
                "Pound": 0.453592,
                "Ounce": 0.0283495,
                "Stone": 6.35029,
                "Ton (US)": 907.185
            },
            "Temperature": {
                "Celsius": "celsius",
                "Fahrenheit": "fahrenheit",
                "Kelvin": "kelvin"
            },
            "Time": {
                "Second": 1.0,
                "Minute": 60.0,
                "Hour": 3600.0,
                "Day": 86400.0,
                "Week": 604800.0,
                "Month (30 days)": 2592000.0,
                "Year (365 days)": 31536000.0,
                "Millisecond": 0.001
            }
        }
        
        # Create GUI components
        self.create_widgets()
        
    def create_widgets(self):
        """Create and layout all GUI widgets."""
        # Title Label
        title_label = tk.Label(
            self.root,
            text="Unit Converter",
            font=("Arial", 18, "bold"),
            pady=10
        )
        title_label.pack()
        
        # Category selection frame
        category_frame = tk.Frame(self.root, pady=10)
        category_frame.pack()
        
        tk.Label(
            category_frame,
            text="Category:",
            font=("Arial", 11)
        ).pack(side=tk.LEFT, padx=5)
        
        # Category dropdown (Level 1)
        self.category_var = tk.StringVar()
        self.category_dropdown = ttk.Combobox(
            category_frame,
            textvariable=self.category_var,
            values=list(self.conversion_data.keys()),
            state="readonly",
            width=15,
            font=("Arial", 10)
        )
        self.category_dropdown.pack(side=tk.LEFT, padx=5)
        self.category_dropdown.current(0)  # Select first category by default
        self.category_dropdown.bind("<<ComboboxSelected>>", self.on_category_change)
        
        # Conversion frame (contains left and right sides)
        conversion_frame = tk.Frame(self.root, pady=20)
        conversion_frame.pack()
        
        # Left side (From)
        left_frame = tk.Frame(conversion_frame)
        left_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(
            left_frame,
            text="From:",
            font=("Arial", 11, "bold")
        ).pack(pady=5)
        
        self.from_unit_var = tk.StringVar()
        self.from_unit_dropdown = ttk.Combobox(
            left_frame,
            textvariable=self.from_unit_var,
            state="readonly",
            width=18,
            font=("Arial", 10)
        )
        self.from_unit_dropdown.pack(pady=5)
        
        # Input textbox
        self.input_var = tk.StringVar(value="0")
        self.input_entry = tk.Entry(
            left_frame,
            textvariable=self.input_var,
            width=20,
            font=("Arial", 11),
            justify="center"
        )
        self.input_entry.pack(pady=5)
        
        # Arrow label
        arrow_label = tk.Label(
            conversion_frame,
            text="→",
            font=("Arial", 24)
        )
        arrow_label.pack(side=tk.LEFT, padx=10)
        
        # Right side (To)
        right_frame = tk.Frame(conversion_frame)
        right_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(
            right_frame,
            text="To:",
            font=("Arial", 11, "bold")
        ).pack(pady=5)
        
        self.to_unit_var = tk.StringVar()
        self.to_unit_dropdown = ttk.Combobox(
            right_frame,
            textvariable=self.to_unit_var,
            state="readonly",
            width=18,
            font=("Arial", 10)
        )
        self.to_unit_dropdown.pack(pady=5)
        
        # Result display
        self.result_var = tk.StringVar(value="0")
        self.result_label = tk.Label(
            right_frame,
            textvariable=self.result_var,
            font=("Arial", 11, "bold"),
            fg="blue",
            relief=tk.SUNKEN,
            width=20,
            height=1,
            bg="white"
        )
        self.result_label.pack(pady=5)
        
        # Convert button
        convert_button = tk.Button(
            self.root,
            text="Convert",
            command=self.convert,
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=5,
            cursor="hand2"
        )
        convert_button.pack(pady=10)
        
        # Initialize unit dropdowns with first category
        self.update_unit_dropdowns()
        
    def on_category_change(self, event=None):
        """Handle category dropdown change event.
        
        Updates the unit dropdowns when a new category is selected.
        """
        self.update_unit_dropdowns()
        # Reset input and result
        self.input_var.set("0")
        self.result_var.set("0")
        
    def update_unit_dropdowns(self):
        """Update unit dropdowns based on selected category."""
        category = self.category_var.get()
        units = list(self.conversion_data[category].keys())
        
        # Update both dropdowns with available units
        self.from_unit_dropdown['values'] = units
        self.to_unit_dropdown['values'] = units
        
        # Set default selections
        if len(units) > 0:
            self.from_unit_dropdown.current(0)
            self.to_unit_dropdown.current(min(1, len(units) - 1))
    
    def convert_temperature(self, value, from_unit, to_unit):
        """Convert temperature between Celsius, Fahrenheit, and Kelvin.
        
        Args:
            value: Temperature value to convert
            from_unit: Source temperature unit
            to_unit: Target temperature unit
            
        Returns:
            Converted temperature value
        """
        # First convert to Celsius as base
        if from_unit == "celsius":
            celsius = value
        elif from_unit == "fahrenheit":
            celsius = (value - 32) * 5 / 9
        elif from_unit == "kelvin":
            celsius = value - 273.15
        else:
            return value
        
        # Then convert from Celsius to target unit
        if to_unit == "celsius":
            return celsius
        elif to_unit == "fahrenheit":
            return celsius * 9 / 5 + 32
        elif to_unit == "kelvin":
            return celsius + 273.15
        else:
            return celsius
    
    def convert(self):
        """Perform unit conversion and display result."""
        try:
            # Get input value
            input_value = float(self.input_var.get())
            
            # Get selected units
            category = self.category_var.get()
            from_unit = self.from_unit_var.get()
            to_unit = self.to_unit_var.get()
            
            # Handle temperature conversion separately (non-linear)
            if category == "Temperature":
                from_type = self.conversion_data[category][from_unit]
                to_type = self.conversion_data[category][to_unit]
                result = self.convert_temperature(input_value, from_type, to_type)
            else:
                # Linear conversion for other categories
                # Convert to base unit first, then to target unit
                from_factor = self.conversion_data[category][from_unit]
                to_factor = self.conversion_data[category][to_unit]
                
                # Convert: input_value * from_factor gives base unit value
                # Then divide by to_factor to get target unit value
                base_value = input_value * from_factor
                result = base_value / to_factor
            
            # Display result with appropriate precision
            if abs(result) < 0.001 or abs(result) > 1000000:
                # Use scientific notation for very small or large numbers
                self.result_var.set(f"{result:.6e}")
            else:
                # Regular decimal notation
                self.result_var.set(f"{result:.6f}".rstrip('0').rstrip('.'))
                
        except ValueError:
            # Show error message for invalid input
            messagebox.showerror(
                "Invalid Input",
                "Please enter a valid numeric value."
            )
            self.input_var.set("0")
            self.result_var.set("0")
        except Exception as e:
            # Handle any other errors
            messagebox.showerror(
                "Conversion Error",
                f"An error occurred: {str(e)}"
            )


def main():
    """Main function to run the Unit Converter application."""
    root = tk.Tk()
    app = UnitConverter(root)
    root.mainloop()


if __name__ == "__main__":
    main()
