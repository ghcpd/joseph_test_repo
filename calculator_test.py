import importlib

import pytest

# Use fake widgets instead of tkinter to avoid GUI dependencies
class FakeEntry:
    def __init__(self):
        self.s = ''
    def get(self):
        return self.s
    def delete(self, start, end):
        self.s = ''
    def insert(self, index, text):
        # emulate tkinter insert appending at end when index is tk.END or 0
        if index == 0:
            self.s = str(text) + self.s
        else:
            self.s += str(text)

class FakeText:
    def __init__(self):
        self.lines = ''
    def delete(self, start, end):
        self.lines = ''
    def insert(self, index, text):
        self.lines += str(text)

@pytest.fixture(autouse=True)
def reload_module_and_setup():
    # Ensure fresh module state each test
    import calculator
    importlib.reload(calculator)
    calculator.entry = FakeEntry()
    calculator.hist_text = FakeText()
    yield


def set_entry(calc, expr):
    calc.entry.delete(0, None)
    calc.entry.insert(None, expr)


def test_decimal_precision_simple():
    import calculator as c
    set_entry(c, '0.1+0.2')
    c.calculate()
    assert c.entry.get() == '0.3'


def test_decimal_precision_chain():
    import calculator as c
    set_entry(c, '0.1+0.2+0.3')
    c.calculate()
    assert c.entry.get() == '0.6'


def test_operator_precedence_and_chain():
    import calculator as c
    set_entry(c, '2+3*4')
    c.calculate()
    assert c.entry.get() == '14'
    # chain
    set_entry(c, '2+3*4-1')
    c.calculate()
    assert c.entry.get() == '13'


def test_division_by_zero_message():
    import calculator as c
    set_entry(c, '5/0')
    c.calculate()
    assert c.entry.get().startswith('Error:')


def test_consecutive_operators_unary_and_invalid():
    import calculator as c
    set_entry(c, '5+-3')
    c.calculate()
    assert c.entry.get() == '2'
    set_entry(c, '6*/2')
    c.calculate()
    assert c.entry.get().startswith('Error:')


def test_reject_multiple_decimals():
    import calculator as c
    set_entry(c, '1..2')
    c.calculate()
    assert c.entry.get().startswith('Error:')
    set_entry(c, '1.2.3')
    c.calculate()
    assert c.entry.get().startswith('Error:')


def test_post_result_input_clears():
    import calculator as c
    set_entry(c, '2+2')
    c.calculate()
    assert c.entry.get() == '4'
    c.press('3')
    assert c.entry.get() == '3'


def test_clear_does_not_erase_history_and_history_fifo():
    import calculator as c
    # Build history with 6 items
    for i in range(6):
        set_entry(c, f'{i}+{i}')
        c.calculate()
    # FIFO size should be 5
    assert len(c.history) == 5
    # First item should be from i=1 now
    assert c.history[0][0] == '1+1'
    # Clear should not erase history
    c.clear()
    assert len(c.history) == 5
    # History text still populated
    assert '1+1 = 2' in c.hist_text.lines


def test_debounce_repeated_digits():
    import calculator as c
    c.entry.delete(0, None)
    c.press('1')
    c.press('1')
    c.press('1')
    assert c.entry.get() == '1'
