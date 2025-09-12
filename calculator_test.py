import builtins
import importlib
import types

# Create stubs for entry and history text widgets
class StubEntry:
    def __init__(self):
        self.buf = ""
    def insert(self, index, text):
        if index == 'end' or index is None:
            self.buf += text
        else:
            # For simplicity append
            self.buf += text
    def delete(self, start, end):
        self.buf = ""
    def get(self):
        return self.buf

class StubText:
    def __init__(self):
        self.text = ""
    def delete(self, start, end):
        self.text = ""
    def insert(self, index, text):
        self.text += text

import calculator as calc

# Attach stubs
calc.entry = StubEntry()
calc.hist_text = StubText()


def test_precision_addition():
    calc.entry.delete(0, None)
    calc.press('0')
    calc.press('.')
    calc.press('1')
    calc.press('+')
    calc.press('0')
    calc.press('.')
    calc.press('2')
    calc.calculate()
    assert calc.entry.get() == '0.3'


def test_precision_chain():
    calc.entry.delete(0, None)
    for ch in '0.1+0.2+0.3':
        calc.press(ch)
    calc.calculate()
    assert calc.entry.get() == '0.6'


def test_operator_precedence():
    calc.entry.delete(0, None)
    for ch in '2+3*4':
        calc.press(ch)
    calc.calculate()
    assert calc.entry.get() == '14'


def test_div_by_zero_message():
    calc.entry.delete(0, None)
    for ch in '5/0':
        calc.press(ch)
    calc.calculate()
    assert calc.entry.get().lower().startswith('error: division by zero')


def test_combined_chain():
    calc.entry.delete(0, None)
    for ch in '2+3*4-1':
        calc.press(ch)
    calc.calculate()
    assert calc.entry.get() == '13'


def test_consecutive_operators_valid_minus():
    calc.entry.delete(0, None)
    for ch in '5+-3':
        calc.press(ch)
    calc.calculate()
    assert calc.entry.get() == '2'


def test_consecutive_operators_invalid():
    calc.entry.delete(0, None)
    for ch in '6*/2':
        calc.press(ch)
    calc.calculate()
    assert calc.entry.get().lower().startswith('error:')


def test_multiple_decimal_points_rejected():
    calc.entry.delete(0, None)
    for ch in '1..2':
        calc.press(ch)
    calc.calculate()
    assert calc.entry.get().lower().startswith('error:')


def test_post_result_clears_on_next_input():
    calc.entry.delete(0, None)
    for ch in '1+1':
        calc.press(ch)
    calc.calculate()
    assert calc.entry.get() == '2'
    # now entering a new digit should clear previous result
    calc.press('3')
    assert calc.entry.get() == '3'


def test_clear_not_erase_history_and_history_fifo():
    calc.entry.delete(0, None)
    # make 6 calculations to exceed history size 5
    for expr in ['1+1','2+2','3+3','4+4','5+5','6+6']:
        calc.entry.delete(0, None)
        for ch in expr:
            calc.press(ch)
        calc.calculate()
    # Clear should not wipe history
    calc.clear()
    assert calc.hist_text.text.strip() != ''
    # Ensure FIFO size 5 and newest 5 are present (2..6)
    lines = [l for l in calc.hist_text.text.strip().split('\n') if l]
    assert len(lines) == 5
    assert lines[0].startswith('2+2')
    assert lines[-1].startswith('6+6')


def test_debounce_repeated_digits():
    calc.entry.delete(0, None)
    calc.press('1')
    calc.press('1')
    calc.press('1')
    assert calc.entry.get() == '1'
