"""Calculator logic: wraps parser and provides memory and history management."""
from typing import List, Tuple
from . import parser

class Calculator:
    def __init__(self) -> None:
        self.memory: float = 0.0
        self.history: List[Tuple[str, str]] = []  # (expr, result or error)

    def evaluate(self, expr: str) -> str:
        try:
            value = parser.evaluate(expr)
            # Limit floating point noise
            result = ("%.*g" % (12, value)).rstrip('.').rstrip('.')
            self._push_history(expr, result)
            return result
        except ZeroDivisionError:
            msg = 'Error: Division by zero'
        except Exception as e:  # noqa: BLE001 - show user-friendly message
            msg = f'Error: {e}'
        self._push_history(expr, msg)
        return msg

    def _push_history(self, expr: str, result: str) -> None:
        self.history.append((expr, result))
        if len(self.history) > 10:
            self.history = self.history[-10:]

    # Memory operations
    def memory_add(self, value: float) -> None:
        self.memory += value

    def memory_subtract(self, value: float) -> None:
        self.memory -= value

    def memory_recall(self) -> float:
        return self.memory

    def memory_clear(self) -> None:
        self.memory = 0.0
