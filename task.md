# 🔹 Prompt: Automated Image Processing Program with GUI

**Task:**
Create a Python program with a GUI to automatically process images in a folder, allowing users to select processing options visually.

---

### 1. **Environment & Setup**

* Python 3.x
* Required libraries: `Pillow`, `numpy`, `Tkinter` (built-in)
* `input/` folder for original images, `output/` folder for processed images

---

### 2. **GUI Requirements**

* Select **input folder** and **output folder**

* Checkboxes or dropdowns for processing options:

  1. Resize (user can set width and height, maintain aspect ratio optional)
  2. Rotate / Flip / Mirror
  3. Filters / Adjustments: Blur, Sharpen, Edge Detection, Brightness, Contrast, Grayscale
  4. Watermark / Text Overlay (user inputs text and position)
  5. Format conversion (JPEG ↔ PNG)

* Optional: Preview processed image before saving

* **Start/Process** button to run batch processing

---

### 3. **Image Processing**

* Use Pillow and Numpy to implement selected transformations
* Batch process all images in input folder
* Save to output folder with naming scheme `originalname_processed.jpg` (or `.png` if converted)

---

### 4. **Constraints**

* Modular and readable code (functions or classes per step)
* Include inline comments
* Handle errors gracefully (e.g., unsupported files, empty folders)
* Provide simple instructions in GUI or popup

---

### How to Run

- Install dependencies:
  - pip install pillow numpy
- Run the GUI app:
  - python app.py
- In the GUI:
  - Use Browse to select input and output folders
  - Configure options (resize, rotate/flip, filters, brightness/contrast, watermark, format)
  - Click Preview First Image to preview transformations
  - Click Process to batch process all supported images in the input folder

Notes:
- In environments without Tkinter/display, the GUI cannot be shown. The image processing functions can still be imported and used programmatically via app.process_image.
