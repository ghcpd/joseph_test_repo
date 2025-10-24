# Unit Converter App

A Tkinter-based desktop utility that converts between units of length, volume,
weight, temperature, and time.

## Running the application

```console
cd unit-converter-app
python -m pip install -r requirements.txt  # optional, see below
python -m unit_converter_app.app
```

The GUI requires an environment with an available display server (e.g. X11 on
Linux or the native windowing system on macOS/Windows). In headless
environments you can still exercise the conversion logic directly:

```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path("unit-converter-app/src")))

from unit_converter_app import convert

print(convert("length", 5, "kilometer", "mile"))
```

## Tests

Run the automated test-suite (conversion logic) with:

```console
cd unit-converter-app
python -m pytest
```

## License

`unit-converter-app` is distributed under the terms of the
[MIT](https://spdx.org/licenses/MIT.html) license.
