## GUI Cauculator bug fixing

You are given a Python module `calculator.py`.
This calculator currently contains multiple defects.
Your task is to **fix the implementation** so that all the following issues are resolved, and then **produce a new test file `calculator_test.py`** (pytest-based) that validates the fixes.

### Known Issues to Fix

1. Floating point precision errors (e.g., `0.1+0.2` should return `0.3`，`0.1+0.2+0.3` should return `0.6`).
2. Operator precedence errors (`2+3*4` should return `14`).
3. Division by zero handling (`5/0` should not yield raw `"Error"`).
4. Combined operator chains must respect precedence (e.g., `2+3*4-1` → `13`).
5. Consecutive operators (`5+-3` should work, invalid forms like `6*/2` should be rejected).
6. Multiple decimal points in a single number must be rejected.
7. Post-result input should clear the previous result instead of appending.
8. Clear button must not erase history.
9. History must be a FIFO of size 5.
10. Rapid repeated digit inputs must debounce (e.g., three presses of `"1"` yield `"1"`, not `"111"`).


### Deliverables

1. A corrected `calculator.py` implementation that addresses all issues.
2. A new `calculator_test.py` file containing pytest tests that cover all issues listed above.

Do not use `eval` or `exec` in your solution.