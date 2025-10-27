from typing import List, Tuple
from parser import evaluate_expression, ParseError

class Calculator:
    """Core calculator handling memory and history using the parser."""

    def __init__(self) -> None:
        self.memory: float = 0.0
        self.history: List[Tuple[str, str]] = []  # (expression, result or error)

    def calculate(self, expr: str) -> str:
        expr = expr.strip()
        if not expr:
            return ''
        try:
            result = evaluate_expression(expr)
            # Trim to reasonable precision
            result_str = ("{:.12g}".format(result))
            self._add_history(expr, result_str)
            return result_str
        except ZeroDivisionError:
            self._add_history(expr, 'Error: Division by zero')
            return 'Error: Division by zero'
        except ParseError as e:
            self._add_history(expr, f'Error: {e}')
            return f'Error: {e}'
        except Exception:
            self._add_history(expr, 'Error')
            return 'Error'

    def _add_history(self, expr: str, result: str) -> None:
        self.history.append((expr, result))
        if len(self.history) > 10:
            self.history = self.history[-10:]

    # Memory functions
    def memory_add(self, value: float) -> None:
        self.memory += value

    def memory_subtract(self, value: float) -> None:
        self.memory -= value

    def memory_recall(self) -> float:
        return self.memory

    def memory_clear(self) -> None:
        self.memory = 0.0
