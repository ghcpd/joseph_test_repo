import tkinter as tk
from ui import CalculatorUI
import os

if __name__ == '__main__':
    root = tk.Tk()
    app = CalculatorUI(root)

    screenshot_path = os.environ.get('SCREENSHOT_PATH')
    if screenshot_path:
        def take_screenshot():
            try:
                os.system(f"scrot {screenshot_path}")
            finally:
                root.destroy()
        root.after(1200, take_screenshot)

    root.mainloop()
