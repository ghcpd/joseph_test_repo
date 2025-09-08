# Scientific Calculator

A desktop scientific calculator application built with Python and Tkinter. This calculator provides a comprehensive set of mathematical functions with a user-friendly graphical interface.

## Features

### Core Functionality
- **Basic Arithmetic**: Addition (+), Subtraction (-), Multiplication (*), Division (/)
- **Scientific Functions**: 
  - Trigonometric: sin(x), cos(x), tan(x)
  - Logarithmic: log(x) (base 10), ln(x) (natural log)
  - Other: sqrt(x) (square root), ^ (exponentiation)
- **Expression Parsing**: Custom parser that evaluates expressions without using Python's `eval()` function
- **Parentheses Support**: Proper grouping of operations with correct precedence
- **Floating Point Numbers**: Support for decimal numbers and negative numbers

### Memory Functions
- **MC (Memory Clear)**: Clear memory
- **MR (Memory Recall)**: Recall value from memory
- **M+ (Memory Add)**: Add current result to memory
- **M- (Memory Subtract)**: Subtract current result from memory

### User Interface
- **Scientific Calculator Layout**: Intuitive button arrangement
- **Display Areas**: 
  - Input display showing current expression
  - Result display showing calculation result
  - Memory indicator showing when memory contains a value
- **History Panel**: Shows last 10 calculations with timestamps
- **Keyboard Support**: Full keyboard input support with shortcuts

### Error Handling
- Division by zero protection
- Invalid expression detection
- Malformed input handling
- Mathematical domain errors (e.g., sqrt of negative numbers)

## Installation and Usage

### Requirements
- Python 3.6 or higher
- Tkinter (usually included with Python)

### Running the Calculator
```bash
python main.py
```

Or make it executable:
```bash
chmod +x main.py
./main.py
```

## Keyboard Shortcuts

| Key | Function |
|-----|----------|
| 0-9 | Digit input |
| +, -, *, / | Basic operators |
| ^ | Exponentiation |
| ( ) | Parentheses |
| . | Decimal point |
| Enter | Calculate |
| Backspace | Delete last character |
| Delete | Clear entry |
| Escape | Clear all |
| s | sin function |
| c | cos function |
| t | tan function |
| l | log function |
| n | ln function |
| r | sqrt function |

## Project Structure

```
scientific-calculator/
├── main.py          # Main entry point
├── parser.py        # Expression parser module
├── calculator.py    # Calculator logic and memory functions
├── ui.py           # Tkinter user interface
└── README.md       # This file
```

### Module Description

#### `parser.py`
- **Tokenizer**: Breaks mathematical expressions into tokens
- **ExpressionParser**: Recursive descent parser that evaluates expressions
- **Custom Functions**: Implementation of mathematical functions without `eval()`
- **Error Handling**: Comprehensive error detection and reporting

#### `calculator.py`
- **Calculator Class**: Main calculator logic
- **Memory Management**: Memory functions (MC, MR, M+, M-)
- **History Management**: Maintains last 10 calculations
- **Result Formatting**: Proper formatting of numerical results

#### `ui.py`
- **CalculatorUI Class**: Complete Tkinter interface
- **Button Layout**: Scientific calculator button arrangement
- **Event Handling**: Mouse and keyboard input processing
- **Display Management**: Input, result, and history displays

#### `main.py`
- **Application Entry Point**: Starts the calculator
- **Error Handling**: Application-level error management
- **Window Management**: Window positioning and closing behavior

## Examples

### Basic Calculations
```
2 + 3 * 4 = 14
(2 + 3) * 4 = 20
sqrt(16) = 4
sin(0) = 0
2^3 = 8
```

### Scientific Functions
```
sin(3.14159/2) ≈ 1
cos(0) = 1
tan(3.14159/4) ≈ 1
log(100) = 2
ln(2.718) ≈ 1
sqrt(25) = 5
```

### Complex Expressions
```
2 * sin(3.14159/6) + log(100) = 3
(sqrt(16) + 2^3) * cos(0) = 12
ln(2.718^2) ≈ 2
```

## Error Messages

The calculator provides clear error messages for various error conditions:

- **Division by zero**: "Error: Division by zero"
- **Invalid input**: "Error: Invalid character 'x' at position y"
- **Unknown function**: "Error: Unknown function: xyz"
- **Mathematical errors**: "Error: Function error in sqrt(-1): math domain error"

## Technical Implementation

### Expression Parsing
The calculator uses a recursive descent parser with the following grammar:

```
expression  := term (('+' | '-') term)*
term        := factor (('*' | '/') factor)*
factor      := power
power       := atom ('^' atom)*
atom        := NUMBER | FUNCTION '(' expression ')' | '(' expression ')' | '-' atom
```

This ensures proper operator precedence:
1. Parentheses and functions (highest)
2. Unary minus
3. Exponentiation (right associative)
4. Multiplication and division
5. Addition and subtraction (lowest)

### Security
The calculator does not use Python's `eval()` function, making it safe from code injection attacks. All mathematical operations are implemented using proper parsing and evaluation techniques.

## Contributing

This calculator was implemented as a demonstration of:
- Clean code organization with separate modules
- Proper error handling and user feedback
- Custom expression parsing without `eval()`
- Professional GUI design with Tkinter
- Comprehensive feature set for scientific calculations

The code is well-documented with docstrings and comments for easy understanding and modification.