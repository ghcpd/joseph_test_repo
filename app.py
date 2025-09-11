import os
import sys
import traceback
try:
    from tkinter import Tk, Label, Entry, Button, Checkbutton, IntVar, filedialog, StringVar, OptionMenu, Scale, HORIZONTAL, Toplevel, messagebox
    from tkinter import ttk
    TK_AVAILABLE = True
except Exception:
    TK_AVAILABLE = False
from PIL import Image, ImageOps, ImageFilter, ImageEnhance, ImageDraw
import numpy as np

# Supported image extensions
SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}


def is_image_file(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in SUPPORTED_EXTS


def apply_edge_detection(img: Image.Image) -> Image.Image:
    # Convert to grayscale for edge detection
    gray = ImageOps.grayscale(img)
    arr = np.array(gray, dtype=np.float32)
    # Simple Laplacian kernel for edge detection
    kernel = np.array([[0, 1, 0],
                       [1, -4, 1],
                       [0, 1, 0]], dtype=np.float32)
    # Pad array
    padded = np.pad(arr, ((1, 1), (1, 1)), mode='edge')
    h, w = arr.shape
    out = np.zeros_like(arr)
    for y in range(h):
        for x in range(w):
            region = padded[y:y+3, x:x+3]
            out[y, x] = np.sum(region * kernel)
    # Normalize to 0-255
    out = np.clip(out + 128, 0, 255).astype(np.uint8)
    # Convert back to RGB
    return Image.fromarray(out).convert('RGB')


def add_watermark(img: Image.Image, text: str, position: str) -> Image.Image:
    if not text:
        return img
    # Create overlay for semi-transparent text
    overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    # Basic text size estimation (no custom font to keep dependencies minimal)
    # Using multiline_textbbox if available, else fallback
    try:
        bbox = draw.multiline_textbbox((0, 0), text)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    except Exception:
        # Fallback approximate size
        text_w = 6 * len(text)
        text_h = 12

    margin = 10
    if position == 'Top-Left':
        xy = (margin, margin)
    elif position == 'Top-Right':
        xy = (img.width - text_w - margin, margin)
    elif position == 'Bottom-Left':
        xy = (margin, img.height - text_h - margin)
    elif position == 'Center':
        xy = ((img.width - text_w) // 2, (img.height - text_h) // 2)
    else:  # Bottom-Right
        xy = (img.width - text_w - margin, img.height - text_h - margin)

    draw.text(xy, text, fill=(255, 255, 255, 160))  # semi-transparent white
    combined = Image.alpha_composite(img.convert('RGBA'), overlay)
    return combined.convert('RGB')


def process_image(img_path: str,
                  resize_w: str,
                  resize_h: str,
                  keep_aspect: bool,
                  rotate_angle: str,
                  flip_h: bool,
                  flip_v: bool,
                  do_blur: bool,
                  do_sharpen: bool,
                  do_edge: bool,
                  do_grayscale: bool,
                  bright_val: int,
                  contrast_val: int,
                  watermark_text: str,
                  watermark_pos: str,
                  target_format: str) -> Image.Image:
    img = Image.open(img_path)
    img = img.convert('RGB')

    # Resize
    if resize_w or resize_h:
        try:
            w = int(resize_w) if resize_w else None
            h = int(resize_h) if resize_h else None
            if keep_aspect:
                if w and not h:
                    ratio = w / img.width
                    h = int(img.height * ratio)
                elif h and not w:
                    ratio = h / img.height
                    w = int(img.width * ratio)
                elif w and h:
                    # Use width as base when both provided
                    ratio = w / img.width
                    h = int(img.height * ratio)
                else:
                    w, h = img.size
            else:
                if not w:
                    w = img.width
                if not h:
                    h = img.height
            img = img.resize((w, h), Image.LANCZOS)
        except Exception:
            # Ignore invalid resize values
            pass

    # Rotate
    try:
        if rotate_angle:
            angle = float(rotate_angle)
            if angle % 360 != 0:
                img = img.rotate(angle, expand=True)
    except Exception:
        pass

    # Flip
    if flip_h:
        img = ImageOps.mirror(img)
    if flip_v:
        img = ImageOps.flip(img)

    # Filters
    if do_blur:
        img = img.filter(ImageFilter.GaussianBlur(radius=2))
    if do_sharpen:
        img = img.filter(ImageFilter.SHARPEN)
    if do_edge:
        img = apply_edge_detection(img)
    if do_grayscale:
        img = ImageOps.grayscale(img).convert('RGB')

    # Brightness and Contrast (scales 0..200, default 100)
    try:
        b_factor = max(0, bright_val) / 100.0
        c_factor = max(0, contrast_val) / 100.0
        if abs(b_factor - 1.0) > 1e-3:
            img = ImageEnhance.Brightness(img).enhance(b_factor)
        if abs(c_factor - 1.0) > 1e-3:
            img = ImageEnhance.Contrast(img).enhance(c_factor)
    except Exception:
        pass

    # Watermark
    img = add_watermark(img, watermark_text, watermark_pos)

    # Format handling is done at save time; just return the image
    return img


class ImageProcessorApp:
    def __init__(self, root):
        self.root = root
        root.title("Automated Image Processing")

        # Instructions
        Label(root, text="Select input and output folders, choose options, then click Process").grid(row=0, column=0, columnspan=6, pady=(10, 10))

        # Folder selection
        Label(root, text="Input Folder:").grid(row=1, column=0, sticky='e')
        self.input_var = StringVar()
        Entry(root, textvariable=self.input_var, width=50).grid(row=1, column=1, columnspan=4, padx=5, pady=5, sticky='we')
        Button(root, text="Browse", command=self.browse_input).grid(row=1, column=5, padx=5)

        Label(root, text="Output Folder:").grid(row=2, column=0, sticky='e')
        self.output_var = StringVar()
        Entry(root, textvariable=self.output_var, width=50).grid(row=2, column=1, columnspan=4, padx=5, pady=5, sticky='we')
        Button(root, text="Browse", command=self.browse_output).grid(row=2, column=5, padx=5)

        # Resize
        Label(root, text="Resize (W x H):").grid(row=3, column=0, sticky='e')
        self.width_var = StringVar()
        self.height_var = StringVar()
        Entry(root, textvariable=self.width_var, width=8).grid(row=3, column=1, sticky='w', padx=2)
        Entry(root, textvariable=self.height_var, width=8).grid(row=3, column=1, sticky='e', padx=2)
        self.aspect_var = IntVar(value=1)
        Checkbutton(root, text="Maintain Aspect", variable=self.aspect_var).grid(row=3, column=2, sticky='w')

        # Rotate / Flip
        Label(root, text="Rotate (deg):").grid(row=4, column=0, sticky='e')
        self.rotate_var = StringVar()
        Entry(root, textvariable=self.rotate_var, width=8).grid(row=4, column=1, sticky='w', padx=2)
        self.flip_h_var = IntVar()
        self.flip_v_var = IntVar()
        Checkbutton(root, text="Flip Horizontal", variable=self.flip_h_var).grid(row=4, column=2, sticky='w')
        Checkbutton(root, text="Flip Vertical", variable=self.flip_v_var).grid(row=4, column=3, sticky='w')

        # Filters
        Label(root, text="Filters:").grid(row=5, column=0, sticky='e')
        self.blur_var = IntVar()
        self.sharpen_var = IntVar()
        self.edge_var = IntVar()
        self.gray_var = IntVar()
        Checkbutton(root, text="Blur", variable=self.blur_var).grid(row=5, column=1, sticky='w')
        Checkbutton(root, text="Sharpen", variable=self.sharpen_var).grid(row=5, column=2, sticky='w')
        Checkbutton(root, text="Edge Detect", variable=self.edge_var).grid(row=5, column=3, sticky='w')
        Checkbutton(root, text="Grayscale", variable=self.gray_var).grid(row=5, column=4, sticky='w')

        # Brightness / Contrast
        Label(root, text="Brightness:").grid(row=6, column=0, sticky='e')
        self.brightness_scale = Scale(root, from_=0, to=200, orient=HORIZONTAL)
        self.brightness_scale.set(100)
        self.brightness_scale.grid(row=6, column=1, columnspan=2, sticky='we', padx=(0, 10))

        Label(root, text="Contrast:").grid(row=6, column=3, sticky='e')
        self.contrast_scale = Scale(root, from_=0, to=200, orient=HORIZONTAL)
        self.contrast_scale.set(100)
        self.contrast_scale.grid(row=6, column=4, columnspan=2, sticky='we', padx=(0, 10))

        # Watermark
        Label(root, text="Watermark Text:").grid(row=7, column=0, sticky='e')
        self.watermark_text_var = StringVar()
        Entry(root, textvariable=self.watermark_text_var, width=30).grid(row=7, column=1, columnspan=2, sticky='we')

        Label(root, text="Position:").grid(row=7, column=3, sticky='e')
        self.position_var = StringVar(value='Bottom-Right')
        OptionMenu(root, self.position_var, 'Top-Left', 'Top-Right', 'Bottom-Left', 'Bottom-Right', 'Center').grid(row=7, column=4, sticky='w')

        # Format conversion
        Label(root, text="Format:").grid(row=8, column=0, sticky='e')
        self.format_var = StringVar(value='Original')
        OptionMenu(root, self.format_var, 'Original', 'JPEG', 'PNG').grid(row=8, column=1, sticky='w')

        # Buttons
        Button(root, text="Preview First Image", command=self.preview_first).grid(row=9, column=1, pady=10)
        Button(root, text="Process", command=self.process_all).grid(row=9, column=2, pady=10)

        for i in range(6):
            root.grid_columnconfigure(i, weight=1)

    def browse_input(self):
        path = filedialog.askdirectory()
        if path:
            self.input_var.set(path)

    def browse_output(self):
        path = filedialog.askdirectory()
        if path:
            self.output_var.set(path)

    def gather_options(self):
        return dict(
            resize_w=self.width_var.get().strip(),
            resize_h=self.height_var.get().strip(),
            keep_aspect=bool(self.aspect_var.get()),
            rotate_angle=self.rotate_var.get().strip(),
            flip_h=bool(self.flip_h_var.get()),
            flip_v=bool(self.flip_v_var.get()),
            do_blur=bool(self.blur_var.get()),
            do_sharpen=bool(self.sharpen_var.get()),
            do_edge=bool(self.edge_var.get()),
            do_grayscale=bool(self.gray_var.get()),
            bright_val=int(self.brightness_scale.get()),
            contrast_val=int(self.contrast_scale.get()),
            watermark_text=self.watermark_text_var.get(),
            watermark_pos=self.position_var.get(),
            target_format=self.format_var.get(),
        )

    def preview_first(self):
        input_dir = self.input_var.get()
        if not input_dir or not os.path.isdir(input_dir):
            messagebox.showerror("Error", "Please select a valid input folder")
            return
        files = [f for f in os.listdir(input_dir) if is_image_file(f)]
        if not files:
            messagebox.showinfo("Info", "No supported images found in input folder")
            return
        first_path = os.path.join(input_dir, files[0])
        try:
            opts = self.gather_options()
            img = process_image(first_path, **opts)
            self.show_preview(img)
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to preview image: {e}")

    def show_preview(self, img: Image.Image):
        top = Toplevel(self.root)
        top.title("Preview")
        # Fit image in a 500x500 box keeping aspect
        max_size = (500, 500)
        preview = ImageOps.contain(img, max_size)
        self._preview_imgtk = ImageOps.exif_transpose(preview)
        try:
            # Lazy import to avoid hard dependency
            from PIL import ImageTk
            imgtk = ImageTk.PhotoImage(self._preview_imgtk)
            label = Label(top, image=imgtk)
            label.image = imgtk
            label.pack(padx=10, pady=10)
        except Exception:
            # If ImageTk not available, just inform user
            Label(top, text="Preview requires Pillow's ImageTk module.").pack(padx=10, pady=10)

    def process_all(self):
        input_dir = self.input_var.get()
        output_dir = self.output_var.get()

        if not input_dir or not os.path.isdir(input_dir):
            messagebox.showerror("Error", "Please select a valid input folder")
            return
        if not output_dir:
            messagebox.showerror("Error", "Please select an output folder")
            return
        os.makedirs(output_dir, exist_ok=True)

        files = [f for f in os.listdir(input_dir) if is_image_file(f)]
        if not files:
            messagebox.showinfo("Info", "No supported images found in input folder")
            return

        opts = self.gather_options()
        processed_count = 0
        errors = []
        for fname in files:
            in_path = os.path.join(input_dir, fname)
            try:
                img = process_image(in_path, **opts)
                base, ext = os.path.splitext(fname)
                fmt = opts['target_format']
                if fmt == 'Original':
                    out_ext = ext.lower()
                    save_format = None  # Pillow infers from extension
                elif fmt == 'JPEG':
                    out_ext = '.jpg'
                    save_format = 'JPEG'
                else:
                    out_ext = '.png'
                    save_format = 'PNG'
                out_name = f"{base}_processed{out_ext}"
                out_path = os.path.join(output_dir, out_name)
                if save_format:
                    img.save(out_path, format=save_format)
                else:
                    img.save(out_path)
                processed_count += 1
            except Exception as e:
                errors.append(f"{fname}: {e}")

        msg = f"Processed {processed_count} images."
        if errors:
            msg += f"\nErrors ({len(errors)}):\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                msg += "\n..."
        messagebox.showinfo("Done", msg)


def main():
    # If running in an environment without a display, fallback to headless info
    if not TK_AVAILABLE:
        print("Tkinter not available; GUI cannot be started in this environment.")
        return 0
    try:
        root = Tk()
    except Exception as e:
        print("Could not start GUI. Make sure a display is available.")
        print(str(e))
        return 1

    app = ImageProcessorApp(root)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == '__main__':
    sys.exit(main())
