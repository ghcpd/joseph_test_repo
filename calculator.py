"""
Calculator Module

This module provides the core calculator functionality including memory operations,
history management, and integration with the expression parser.
"""

from typing import List, Optional, Tuple
import time
from parser import evaluate_expression, ParseError


class Calculator:
    """
    Main calculator class that manages calculations, memory, and history.
    """
    
    def __init__(self):
        self.memory: float = 0.0
        self.history: List[Tuple[str, str, str]] = []  # (expression, result, timestamp)
        self.max_history = 10
    
    def calculate(self, expression: str) -> str:
        """
        Evaluate a mathematical expression and update history.
        
        Args:
            expression: The mathematical expression to evaluate
            
        Returns:
            String representation of the result or error message
        """
        try:
            # Remove any whitespace
            expression = expression.strip()
            
            if not expression:
                return "0"
            
            # Evaluate the expression
            result = evaluate_expression(expression)
            
            # Format the result
            result_str = self._format_result(result)
            
            # Add to history
            self._add_to_history(expression, result_str)
            
            return result_str
            
        except ZeroDivisionError:
            error_msg = "Error: Division by zero"
            self._add_to_history(expression, error_msg)
            return error_msg
            
        except ParseError as e:
            error_msg = f"Error: {str(e)}"
            self._add_to_history(expression, error_msg)
            return error_msg
            
        except (ValueError, OverflowError) as e:
            error_msg = f"Error: {str(e)}"
            self._add_to_history(expression, error_msg)
            return error_msg
            
        except Exception as e:
            error_msg = f"Error: Unexpected error - {str(e)}"
            self._add_to_history(expression, error_msg)
            return error_msg
    
    def _format_result(self, result: float) -> str:
        """
        Format a numerical result for display.
        
        Args:
            result: The numerical result to format
            
        Returns:
            Formatted string representation
        """
        # Handle special cases
        if result == float('inf'):
            return "∞"
        elif result == float('-inf'):
            return "-∞"
        elif result != result:  # NaN check
            return "Error: Invalid result"
        
        # Format based on magnitude and precision
        abs_result = abs(result)
        
        # For very large or very small numbers, use scientific notation
        if abs_result > 1e15 or (abs_result < 1e-6 and abs_result != 0):
            return f"{result:.6e}"
        
        # For integers, show as integer
        if result == int(result):
            return str(int(result))
        
        # For floats, limit decimal places
        formatted = f"{result:.10f}".rstrip('0').rstrip('.')
        return formatted if formatted else "0"
    
    def _add_to_history(self, expression: str, result: str):
        """
        Add a calculation to the history.
        
        Args:
            expression: The expression that was evaluated
            result: The result or error message
        """
        timestamp = time.strftime("%H:%M:%S")
        self.history.append((expression, result, timestamp))
        
        # Keep only the last max_history entries
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def get_history(self) -> List[Tuple[str, str, str]]:
        """
        Get the calculation history.
        
        Returns:
            List of tuples (expression, result, timestamp)
        """
        return self.history.copy()
    
    def clear_history(self):
        """Clear the calculation history."""
        self.history.clear()
    
    # Memory functions
    
    def memory_clear(self):
        """Clear memory (MC - Memory Clear)."""
        self.memory = 0.0
    
    def memory_recall(self) -> str:
        """Recall value from memory (MR - Memory Recall)."""
        return self._format_result(self.memory)
    
    def memory_add(self, value_str: str) -> str:
        """
        Add value to memory (M+ - Memory Add).
        
        Args:
            value_str: String representation of value to add
            
        Returns:
            Formatted memory value or error message
        """
        try:
            if value_str.strip():
                value = evaluate_expression(value_str)
                self.memory += value
            return self._format_result(self.memory)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def memory_subtract(self, value_str: str) -> str:
        """
        Subtract value from memory (M- - Memory Subtract).
        
        Args:
            value_str: String representation of value to subtract
            
        Returns:
            Formatted memory value or error message
        """
        try:
            if value_str.strip():
                value = evaluate_expression(value_str)
                self.memory -= value
            return self._format_result(self.memory)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def memory_store(self, value_str: str) -> str:
        """
        Store value in memory (MS - Memory Store).
        
        Args:
            value_str: String representation of value to store
            
        Returns:
            Formatted memory value or error message
        """
        try:
            if value_str.strip():
                self.memory = evaluate_expression(value_str)
            else:
                self.memory = 0.0
            return self._format_result(self.memory)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_memory(self) -> float:
        """Get the current memory value."""
        return self.memory
    
    def has_memory(self) -> bool:
        """Check if memory contains a non-zero value."""
        return self.memory != 0.0


if __name__ == "__main__":
    # Test the calculator
    calc = Calculator()
    
    print("Testing Calculator:")
    print("==================")
    
    # Test basic calculations
    test_cases = [
        "2 + 3",
        "5 * 4",
        "sqrt(16)",
        "sin(0)",
        "10 / 0",  # Division by zero
        "invalid expression",  # Parse error
        "2^3",
        "log(100)",
    ]
    
    for expr in test_cases:
        result = calc.calculate(expr)
        print(f"{expr} = {result}")
    
    print("\nHistory:")
    for expr, result, timestamp in calc.get_history():
        print(f"{timestamp}: {expr} = {result}")
    
    print("\nTesting memory functions:")
    print(f"Memory recall: {calc.memory_recall()}")
    print(f"Memory store 42: {calc.memory_store('42')}")
    print(f"Memory add 8: {calc.memory_add('8')}")
    print(f"Memory recall: {calc.memory_recall()}")
    print(f"Memory subtract 10: {calc.memory_subtract('10')}")
    print(f"Memory recall: {calc.memory_recall()}")
    print(f"Has memory: {calc.has_memory()}")
    calc.memory_clear()
    print(f"After clear - Memory recall: {calc.memory_recall()}")
    print(f"Has memory: {calc.has_memory()}")