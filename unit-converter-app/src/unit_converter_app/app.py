"""Tkinter GUI application wrapping the conversion logic."""
from __future__ import annotations

import tkinter as tk
from typing import Iterable

from . import converter


class UnitConverterApp:
    """Simple Tkinter based unit converter GUI."""

    def __init__(self, root: tk.Tk) -> None:
        # Build widgets
        self.root = root
        root.title("Unit Converter")

        self.category_var = tk.StringVar(value="length")
        self.from_unit_var = tk.StringVar()
        self.to_unit_var = tk.StringVar()
        self.input_var = tk.StringVar()
        self.result_var = tk.StringVar()

        # Layout containers (grid for clarity)
        root.columnconfigure(1, weight=1)

        tk.Label(root, text="Category").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.category_menu = tk.OptionMenu(root, self.category_var, *converter.list_categories())
        self.category_menu.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(root, text="From").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.from_menu = tk.OptionMenu(root, self.from_unit_var, "")
        self.from_menu.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(root, text="To").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.to_menu = tk.OptionMenu(root, self.to_unit_var, "")
        self.to_menu.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(root, text="Value").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.input_entry = tk.Entry(root, textvariable=self.input_var)
        self.input_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        self.convert_button = tk.Button(root, text="Convert", command=self.on_convert)
        self.convert_button.grid(row=4, column=0, columnspan=2, padx=5, pady=10)

        tk.Label(root, text="Result").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.result_label = tk.Label(root, textvariable=self.result_var, relief=tk.SUNKEN)
        self.result_label.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

        # Bindings
        self.category_var.trace_add("write", self.on_category_change)

        # Initialize choices
        self.refresh_units(self.category_var.get())

    # GUI helper operations -------------------------------------------------
    def refresh_units(self, category: str) -> None:
        """Refresh dropdown options whenever the category changes."""

        units = list(converter.list_units(category))
        self._reset_option_menu(self.from_menu, self.from_unit_var, units)
        self._reset_option_menu(self.to_menu, self.to_unit_var, units)

    def _reset_option_menu(
        self, menu: tk.OptionMenu, variable: tk.StringVar, options: Iterable[str]
    ) -> None:
        menu["menu"].delete(0, "end")
        for choice in options:
            menu["menu"].add_command(label=choice, command=tk._setit(variable, choice))
        first_option = next(iter(options), "")
        variable.set(first_option)

    # Event handlers --------------------------------------------------------
    def on_category_change(self, *_: object) -> None:
        category = self.category_var.get()
        self.refresh_units(category)
        self.result_var.set("")

    def on_convert(self) -> None:
        value_text = self.input_var.get().strip()
        try:
            value = float(value_text)
        except ValueError:
            self.result_var.set("Invalid number")
            return

        category = self.category_var.get()
        from_unit = self.from_unit_var.get()
        to_unit = self.to_unit_var.get()

        try:
            converted = converter.convert(category, value, from_unit, to_unit)
        except (converter.UnknownCategoryError, converter.UnknownUnitError) as error:
            self.result_var.set(str(error))
            return

        self.result_var.set(f"{converted:.6g}")


def main() -> None:
    root = tk.Tk()
    UnitConverterApp(root)
    root.mainloop()


if __name__ == "__main__":  # pragma: no cover
    main()
