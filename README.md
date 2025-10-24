# Unit Converter GUI Application

A professional Python GUI application built with Tkinter for converting between different units across multiple categories.

## Features

### Supported Categories
- **Length**: Meter, Kilometer, Centimeter, Millimeter, Mile, Yard, Foot, Inch
- **Volume**: Liter, Milliliter, Gallon (US), Quart (US), Pint (US), Cup (US), Fluid Ounce (US), Cubic Meter, Cubic Centimeter
- **Weight**: Kilogram, Gram, Milligram, Metric Ton, Pound, Ounce, Stone, Ton (US)
- **Temperature**: Celsius, Fahrenheit, Kelvin
- **Time**: Second, Minute, Hour, Day, Week, Month (30 days), Year (365 days)

### Key Capabilities
✅ **Dynamic Interface**: Unit dropdowns automatically update when you change the category
✅ **Accurate Conversions**: Handles both linear conversions and special temperature formulas
✅ **Input Validation**: Accepts integers and decimal numbers, with error handling for invalid input
✅ **Smart Output**: Automatically formats results, removing unnecessary trailing zeros
✅ **User-Friendly**: Clean, intuitive interface with clear labels and helpful guidance

## Requirements

- Python 3.x
- Tkinter (usually included with Python)

## Installation

### On Ubuntu/Debian
```bash
sudo apt-get install python3-tk
```

### On macOS
Tkinter is usually included with Python. If not:
```bash
brew install python-tk
```

### On Windows
Tkinter is included with the standard Python installer.

## Usage

Run the application:
```bash
python3 unit_converter.py
```

### How to Use
1. Select a category from the top dropdown (Length, Volume, Weight, Temperature, or Time)
2. Enter a numeric value in the "From" input box
3. Select the source unit from the left dropdown
4. Select the target unit from the right dropdown
5. Click the "Convert" button to see the result

### Example Conversions
- **Length**: 5 km → 3.10686 miles
- **Temperature**: 100°C → 212°F
- **Weight**: 1 kg → 2.20462 pounds
- **Volume**: 1 liter → 0.264172 US gallons
- **Time**: 1 hour → 60 minutes

## Code Structure

The application is organized as a single class `UnitConverter` with the following methods:

- `__init__()`: Initializes the application and conversion data
- `create_widgets()`: Creates and layouts all GUI components
- `update_unit_dropdowns()`: Updates unit selectors when category changes
- `convert_temperature()`: Handles special temperature conversions
- `convert()`: Main conversion logic with input validation

## Technical Details

### Conversion Algorithm
For most units (length, volume, weight, time):
1. Convert input value to a base unit (e.g., meters for length)
2. Convert from base unit to target unit

For temperature:
- Special formulas are used as temperature conversions are not linear
- Celsius is used as the intermediate unit

### Input Validation
- Accepts positive and negative numbers
- Accepts decimal values
- Shows error dialog for non-numeric input
- Handles edge cases gracefully

## Screenshots

![Unit Converter Application](https://github.com/user-attachments/assets/150f20aa-7281-41a5-9893-35d5e8babd4a)

The application demonstrates:
1. Clean, professional interface
2. Dynamic category switching
3. Accurate conversions across all categories
4. User-friendly error handling

## License

This project is open source and available for educational purposes.

## Author

Created as a demonstration of Tkinter GUI development in Python.
