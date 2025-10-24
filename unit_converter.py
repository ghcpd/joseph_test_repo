#!/usr/bin/env python3
"""
Unit Converter GUI Application
A Tkinter-based application for converting between different units across multiple categories.
"""

import tkinter as tk
from tkinter import ttk, messagebox


class UnitConverter:
    """
    Main class for the Unit Converter application.
    Handles GUI creation and conversion logic.
    """
    
    def __init__(self, root):
        """Initialize the Unit Converter application."""
        self.root = root
        self.root.title("Unit Converter")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        # Define conversion data for each category
        # Each category contains units with their conversion factors to a base unit
        self.conversion_data = {
            "Length": {
                "Meter": 1.0,
                "Kilometer": 0.001,
                "Centimeter": 100.0,
                "Millimeter": 1000.0,
                "Mile": 0.000621371,
                "Yard": 1.09361,
                "Foot": 3.28084,
                "Inch": 39.3701
            },
            "Volume": {
                "Liter": 1.0,
                "Milliliter": 1000.0,
                "Gallon (US)": 0.264172,
                "Quart (US)": 1.05669,
                "Pint (US)": 2.11338,
                "Cup (US)": 4.22675,
                "Fluid Ounce (US)": 33.814,
                "Cubic Meter": 0.001,
                "Cubic Centimeter": 1000.0
            },
            "Weight": {
                "Kilogram": 1.0,
                "Gram": 1000.0,
                "Milligram": 1000000.0,
                "Metric Ton": 0.001,
                "Pound": 2.20462,
                "Ounce": 35.274,
                "Stone": 0.157473,
                "Ton (US)": 0.00110231
            },
            "Temperature": {
                "Celsius": "C",
                "Fahrenheit": "F",
                "Kelvin": "K"
            },
            "Time": {
                "Second": 1.0,
                "Minute": 0.0166667,
                "Hour": 0.000277778,
                "Day": 0.0000115741,
                "Week": 0.00000165344,
                "Month (30 days)": 0.000000380518,
                "Year (365 days)": 0.0000000316888
            }
        }
        
        # Create GUI components
        self.create_widgets()
    
    def create_widgets(self):
        """Create and layout all GUI widgets."""
        # Main title
        title_label = tk.Label(
            self.root, 
            text="Unit Converter", 
            font=("Arial", 24, "bold"),
            pady=20
        )
        title_label.pack()
        
        # Category selection frame
        category_frame = tk.Frame(self.root)
        category_frame.pack(pady=10)
        
        tk.Label(
            category_frame, 
            text="Category:", 
            font=("Arial", 12)
        ).pack(side=tk.LEFT, padx=5)
        
        # Category dropdown (Level 1)
        self.category_var = tk.StringVar()
        self.category_dropdown = ttk.Combobox(
            category_frame,
            textvariable=self.category_var,
            values=list(self.conversion_data.keys()),
            state="readonly",
            width=20,
            font=("Arial", 11)
        )
        self.category_dropdown.pack(side=tk.LEFT, padx=5)
        self.category_dropdown.current(0)  # Default to first category
        self.category_dropdown.bind("<<ComboboxSelected>>", self.update_unit_dropdowns)
        
        # Conversion frame
        conversion_frame = tk.Frame(self.root)
        conversion_frame.pack(pady=20)
        
        # Left side (From)
        left_frame = tk.Frame(conversion_frame)
        left_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(
            left_frame, 
            text="From:", 
            font=("Arial", 12, "bold")
        ).pack(pady=5)
        
        # Input value textbox
        self.input_var = tk.StringVar()
        self.input_entry = tk.Entry(
            left_frame,
            textvariable=self.input_var,
            font=("Arial", 14),
            width=15,
            justify="center"
        )
        self.input_entry.pack(pady=5)
        self.input_entry.insert(0, "1")  # Default value
        
        # From unit dropdown (Level 2 left)
        self.from_unit_var = tk.StringVar()
        self.from_unit_dropdown = ttk.Combobox(
            left_frame,
            textvariable=self.from_unit_var,
            state="readonly",
            width=18,
            font=("Arial", 11)
        )
        self.from_unit_dropdown.pack(pady=5)
        
        # Right side (To)
        right_frame = tk.Frame(conversion_frame)
        right_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(
            right_frame, 
            text="To:", 
            font=("Arial", 12, "bold")
        ).pack(pady=5)
        
        # Output value label
        self.output_var = tk.StringVar()
        self.output_var.set("0")
        output_label = tk.Label(
            right_frame,
            textvariable=self.output_var,
            font=("Arial", 14),
            width=15,
            relief="sunken",
            bg="white",
            anchor="center",
            height=1
        )
        output_label.pack(pady=5)
        
        # To unit dropdown (Level 2 right)
        self.to_unit_var = tk.StringVar()
        self.to_unit_dropdown = ttk.Combobox(
            right_frame,
            textvariable=self.to_unit_var,
            state="readonly",
            width=18,
            font=("Arial", 11)
        )
        self.to_unit_dropdown.pack(pady=5)
        
        # Convert button
        convert_button = tk.Button(
            self.root,
            text="Convert",
            command=self.convert,
            font=("Arial", 14, "bold"),
            bg="#4CAF50",
            fg="white",
            padx=30,
            pady=10,
            cursor="hand2"
        )
        convert_button.pack(pady=20)
        
        # Information label
        info_label = tk.Label(
            self.root,
            text="Enter a value and click Convert",
            font=("Arial", 10),
            fg="gray"
        )
        info_label.pack(pady=10)
        
        # Initialize unit dropdowns with default category
        self.update_unit_dropdowns()
    
    def update_unit_dropdowns(self, event=None):
        """
        Update the from and to unit dropdowns based on selected category.
        Called when category dropdown selection changes.
        """
        category = self.category_var.get()
        units = list(self.conversion_data[category].keys())
        
        # Update both dropdowns with units from selected category
        self.from_unit_dropdown['values'] = units
        self.to_unit_dropdown['values'] = units
        
        # Set default selections
        if len(units) > 0:
            self.from_unit_dropdown.current(0)
            self.to_unit_dropdown.current(min(1, len(units) - 1))
        
        # Clear output when category changes
        self.output_var.set("0")
    
    def convert_temperature(self, value, from_unit, to_unit):
        """
        Special conversion function for temperature units.
        Temperature conversions are not linear and require special handling.
        
        Args:
            value: The numeric value to convert
            from_unit: Source temperature unit
            to_unit: Target temperature unit
        
        Returns:
            Converted temperature value
        """
        # Convert to Celsius first (as base unit)
        if from_unit == "Celsius":
            celsius = value
        elif from_unit == "Fahrenheit":
            celsius = (value - 32) * 5/9
        elif from_unit == "Kelvin":
            celsius = value - 273.15
        
        # Convert from Celsius to target unit
        if to_unit == "Celsius":
            result = celsius
        elif to_unit == "Fahrenheit":
            result = celsius * 9/5 + 32
        elif to_unit == "Kelvin":
            result = celsius + 273.15
        
        return result
    
    def convert(self):
        """
        Perform the conversion based on selected units and input value.
        Handles validation and calls appropriate conversion logic.
        """
        try:
            # Get input value and validate it's a number
            input_value = float(self.input_var.get())
            
            category = self.category_var.get()
            from_unit = self.from_unit_var.get()
            to_unit = self.to_unit_var.get()
            
            # Check if units are selected
            if not from_unit or not to_unit:
                messagebox.showwarning("Warning", "Please select both units")
                return
            
            # Handle temperature conversion separately (non-linear)
            if category == "Temperature":
                result = self.convert_temperature(input_value, from_unit, to_unit)
            else:
                # For linear conversions, convert to base unit first, then to target unit
                conversion_factors = self.conversion_data[category]
                
                # Convert input to base unit
                base_value = input_value / conversion_factors[from_unit]
                
                # Convert from base unit to target unit
                result = base_value * conversion_factors[to_unit]
            
            # Format result to remove unnecessary decimals
            if result == int(result):
                self.output_var.set(str(int(result)))
            else:
                # Show up to 6 decimal places, removing trailing zeros
                self.output_var.set(f"{result:.6f}".rstrip('0').rstrip('.'))
        
        except ValueError:
            # Handle invalid input (non-numeric)
            messagebox.showerror("Error", "Please enter a valid number")
            self.output_var.set("0")
        except Exception as e:
            # Handle any other errors
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.output_var.set("0")


def main():
    """Main function to run the application."""
    root = tk.Tk()
    app = UnitConverter(root)
    root.mainloop()


if __name__ == "__main__":
    main()
