#!/usr/bin/env python3
"""
Test suite for the Scientific Calculator

This module contains tests to verify the functionality of the calculator
components: parser, calculator logic, and basic integration.
"""

import sys
import os
import math

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parser import evaluate_expression, ParseError
from calculator import Calculator


def test_parser():
    """Test the expression parser functionality."""
    print("Testing Expression Parser...")
    
    test_cases = [
        # Basic arithmetic
        ("2 + 3", 5.0),
        ("10 - 4", 6.0),
        ("3 * 4", 12.0),
        ("15 / 3", 5.0),
        
        # Operator precedence
        ("2 + 3 * 4", 14.0),
        ("(2 + 3) * 4", 20.0),
        ("2 * 3 + 4", 10.0),
        
        # Scientific functions
        ("sin(0)", 0.0),
        ("cos(0)", 1.0),
        ("sqrt(16)", 4.0),
        ("sqrt(25)", 5.0),
        ("log(100)", 2.0),
        ("2^3", 8.0),
        ("3^2", 9.0),
        
        # Negative numbers
        ("-5", -5.0),
        ("2 + (-3)", -1.0),
        ("2 * -3", -6.0),
        
        # Complex expressions
        ("sqrt(16) + 2^3", 12.0),
        ("sin(0) + cos(0)", 1.0),
        ("(2 + 3) * (4 - 1)", 15.0),
    ]
    
    passed = 0
    failed = 0
    
    for expression, expected in test_cases:
        try:
            result = evaluate_expression(expression)
            if abs(result - expected) < 1e-10:  # Allow for floating point precision
                print(f"  ✓ {expression} = {result}")
                passed += 1
            else:
                print(f"  ✗ {expression} = {result} (expected {expected})")
                failed += 1
        except Exception as e:
            print(f"  ✗ {expression} failed with error: {e}")
            failed += 1
    
    # Test error cases
    error_cases = [
        "1 / 0",  # Division by zero
        "sqrt(-1)",  # Domain error
        "invalid",  # Parse error
        "2 +",  # Incomplete expression
        ")",  # Mismatched parentheses
    ]
    
    print("\nTesting error handling...")
    for expression in error_cases:
        try:
            result = evaluate_expression(expression)
            print(f"  ✗ {expression} should have failed but returned {result}")
            failed += 1
        except (ParseError, ZeroDivisionError, ValueError) as e:
            print(f"  ✓ {expression} correctly failed: {type(e).__name__}")
            passed += 1
        except Exception as e:
            print(f"  ? {expression} failed with unexpected error: {e}")
            # This might be acceptable depending on the error
    
    print(f"\nParser Tests: {passed} passed, {failed} failed")
    return failed == 0


def test_calculator():
    """Test the calculator functionality."""
    print("\nTesting Calculator...")
    
    calc = Calculator()
    passed = 0
    failed = 0
    
    # Test basic calculations
    test_cases = [
        ("2 + 3", "5"),
        ("sqrt(16)", "4"),
        ("sin(0)", "0"),
        ("2^3", "8"),
        ("log(100)", "2"),
    ]
    
    for expression, expected in test_cases:
        result = calc.calculate(expression)
        if result == expected:
            print(f"  ✓ {expression} = {result}")
            passed += 1
        else:
            print(f"  ✗ {expression} = {result} (expected {expected})")
            failed += 1
    
    # Test memory functions
    print("\nTesting memory functions...")
    
    # Clear memory first
    calc.memory_clear()
    if calc.memory_recall() == "0":
        print("  ✓ Memory clear works")
        passed += 1
    else:
        print("  ✗ Memory clear failed")
        failed += 1
    
    # Store value
    calc.memory_store("42")
    if calc.memory_recall() == "42":
        print("  ✓ Memory store works")
        passed += 1
    else:
        print("  ✗ Memory store failed")
        failed += 1
    
    # Add to memory
    calc.memory_add("8")
    if calc.memory_recall() == "50":
        print("  ✓ Memory add works")
        passed += 1
    else:
        print("  ✗ Memory add failed")
        failed += 1
    
    # Subtract from memory
    calc.memory_subtract("10")
    if calc.memory_recall() == "40":
        print("  ✓ Memory subtract works")
        passed += 1
    else:
        print("  ✗ Memory subtract failed")
        failed += 1
    
    # Test history
    print("\nTesting history...")
    history = calc.get_history()
    if len(history) >= 5:  # Should have at least the test calculations
        print(f"  ✓ History contains {len(history)} entries")
        passed += 1
    else:
        print(f"  ✗ History only contains {len(history)} entries")
        failed += 1
    
    # Test error handling
    print("\nTesting error handling...")
    error_result = calc.calculate("1 / 0")
    if "Error" in error_result:
        print(f"  ✓ Division by zero handled: {error_result}")
        passed += 1
    else:
        print(f"  ✗ Division by zero not handled properly: {error_result}")
        failed += 1
    
    print(f"\nCalculator Tests: {passed} passed, {failed} failed")
    return failed == 0


def test_integration():
    """Test integration between components."""
    print("\nTesting Integration...")
    
    # Test that all modules can be imported together
    try:
        import parser
        import calculator
        # Note: We can't test ui module in headless environment
        print("  ✓ All modules import successfully")
        return True
    except Exception as e:
        print(f"  ✗ Module import failed: {e}")
        return False


def main():
    """Run all tests."""
    print("Scientific Calculator Test Suite")
    print("=" * 40)
    
    parser_ok = test_parser()
    calculator_ok = test_calculator()
    integration_ok = test_integration()
    
    print("\n" + "=" * 40)
    if parser_ok and calculator_ok and integration_ok:
        print("All tests PASSED! ✓")
        print("\nThe calculator is ready to use.")
        print("Run 'python3 main.py' to start the application.")
        return 0
    else:
        print("Some tests FAILED! ✗")
        return 1


if __name__ == "__main__":
    sys.exit(main())