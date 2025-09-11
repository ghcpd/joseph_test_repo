#!/usr/bin/env python3
# Simple Tkinter GUI batch image processor using Pillow and NumPy
# Requirements: Pillow, numpy (Tkinter is built-in)
# This app lets you pick input/output folders and choose processing options.

import os
import sys
import traceback
from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageOps, ImageDraw, ImageFont, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox

SUPPORTED_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}

@dataclass
class Options:
    resize: bool = False
    width: Optional[int] = None
    height: Optional[int] = None
    maintain_aspect: bool = True

    transform: str = "None"  # choices: None, Rotate 90/180/270, Flip Horizontal, Flip Vertical, Mirror

    blur: bool = False
    sharpen: bool = False
    edge: bool = False
    brightness: float = 1.0
    contrast: float = 1.0
    grayscale: bool = False

    watermark_text: str = ""
    watermark_pos: str = "bottom-right"  # TL, TR, center, BL, BR

    target_format: str = "Original"  # Original, JPEG, PNG


def is_image_file(path: str) -> bool:
    _, ext = os.path.splitext(path.lower())
    return ext in SUPPORTED_EXT


def apply_resize(img: Image.Image, width: Optional[int], height: Optional[int], maintain_aspect: bool) -> Image.Image:
    if not width and not height:
        return img
    if maintain_aspect:
        # Compute new size maintaining aspect ratio
        w, h = img.size
        if width and height:
            # Fit within box
            img = ImageOps.contain(img, (width, height))
        elif width:
            ratio = width / w
            img = img.resize((width, int(h * ratio)))
        elif height:
            ratio = height / h
            img = img.resize((int(w * ratio), height))
        return img
    else:
        return img.resize((width or img.width, height or img.height))


def apply_transform(img: Image.Image, transform: str) -> Image.Image:
    t = transform.lower()
    if "rotate 90" in t:
        return img.rotate(90, expand=True)
    if "rotate 180" in t:
        return img.rotate(180, expand=True)
    if "rotate 270" in t:
        return img.rotate(270, expand=True)
    if "flip horizontal" in t or "mirror" in t:
        return ImageOps.mirror(img)
    if "flip vertical" in t:
        return ImageOps.flip(img)
    return img


def apply_edge_detection_numpy(img: Image.Image) -> Image.Image:
    # Convert to grayscale ndarray
    gray = ImageOps.grayscale(img)
    arr = np.array(gray, dtype=float)
    # Sobel kernels
    Kx = np.array([[1, 0, -1], [2, 0, -2], [1, 0, -1]], dtype=float)
    Ky = np.array([[1, 2, 1], [0, 0, 0], [-1, -2, -1]], dtype=float)
    # Convolve
    def convolve(a, k):
        h, w = a.shape
        kh, kw = k.shape
        pad_h, pad_w = kh // 2, kw // 2
        padded = np.pad(a, ((pad_h, pad_h), (pad_w, pad_w)), mode='edge')
        out = np.zeros_like(a)
        for i in range(h):
            for j in range(w):
                region = padded[i:i+kh, j:j+kw]
                out[i, j] = np.sum(region * k)
        return out
    gx = convolve(arr, Kx)
    gy = convolve(arr, Ky)
    mag = np.hypot(gx, gy)
    mag = (mag / (mag.max() + 1e-9) * 255).astype(np.uint8)
    return Image.fromarray(mag)


def apply_filters(img: Image.Image, opts: Options) -> Image.Image:
    out = img
    if opts.blur:
        out = out.filter(ImageFilter.BLUR)
    if opts.sharpen:
        out = out.filter(ImageFilter.SHARPEN)
    if opts.edge:
        out = apply_edge_detection_numpy(out)
    if abs(opts.brightness - 1.0) > 1e-3:
        out = ImageEnhance.Brightness(out).enhance(opts.brightness)
    if abs(opts.contrast - 1.0) > 1e-3:
        out = ImageEnhance.Contrast(out).enhance(opts.contrast)
    if opts.grayscale:
        out = ImageOps.grayscale(out)
    return out


def apply_watermark(img: Image.Image, text: str, pos: str) -> Image.Image:
    if not text:
        return img
    out = img.copy()
    draw = ImageDraw.Draw(out)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    margin = 10
    W, H = out.size
    pos_map = {
        "top-left": (margin, margin),
        "top-right": (W - text_w - margin, margin),
        "center": ((W - text_w) // 2, (H - text_h) // 2),
        "bottom-left": (margin, H - text_h - margin),
        "bottom-right": (W - text_w - margin, H - text_h - margin),
    }
    xy = pos_map.get(pos, (W - text_w - margin, H - text_h - margin))
    draw.text(xy, text, fill=(255, 255, 255), font=font, stroke_width=1, stroke_fill=(0, 0, 0))
    return out


def process_image(path: str, opts: Options) -> Optional[Image.Image]:
    try:
        with Image.open(path) as im:
            im = im.convert("RGB")
            if opts.resize:
                im = apply_resize(im, opts.width, opts.height, opts.maintain_aspect)
            im = apply_transform(im, opts.transform)
            im = apply_filters(im, opts)
            im = apply_watermark(im, opts.watermark_text, opts.watermark_pos)
            return im
    except Exception:
        return None


def save_output(img: Image.Image, original_name: str, out_dir: str, target_format: str) -> str:
    base, _ = os.path.splitext(os.path.basename(original_name))
    ext = ".jpg"
    save_fmt = "JPEG"
    if target_format.upper() == "PNG":
        ext = ".png"
        save_fmt = "PNG"
    elif target_format == "Original":
        # Preserve if PNG else save JPEG
        if original_name.lower().endswith(".png"):
            ext = ".png"
            save_fmt = "PNG"
    out_path = os.path.join(out_dir, f"{base}_processed{ext}")
    img.save(out_path, save_fmt)
    return out_path


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Image Processor")

        # Paths
        base = "/home/runner/work/joseph_test_repo/joseph_test_repo"
        self.input_var = tk.StringVar(value=os.path.join(base, "input"))
        self.output_var = tk.StringVar(value=os.path.join(base, "output"))

        row = 0
        tk.Label(root, text="Input Folder:").grid(row=row, column=0, sticky="w")
        tk.Entry(root, textvariable=self.input_var, width=50).grid(row=row, column=1)
        tk.Button(root, text="Browse", command=self.browse_input).grid(row=row, column=2)
        row += 1
        tk.Label(root, text="Output Folder:").grid(row=row, column=0, sticky="w")
        tk.Entry(root, textvariable=self.output_var, width=50).grid(row=row, column=1)
        tk.Button(root, text="Browse", command=self.browse_output).grid(row=row, column=2)

        # Resize
        row += 1
        self.resize_var = tk.BooleanVar()
        tk.Checkbutton(root, text="Resize", variable=self.resize_var).grid(row=row, column=0, sticky="w")
        self.width_var = tk.StringVar(value="")
        self.height_var = tk.StringVar(value="")
        tk.Label(root, text="W:").grid(row=row, column=1, sticky="e")
        tk.Entry(root, textvariable=self.width_var, width=6).grid(row=row, column=1, sticky="w", padx=(25,0))
        tk.Label(root, text="H:").grid(row=row, column=1, sticky="e", padx=(80,0))
        tk.Entry(root, textvariable=self.height_var, width=6).grid(row=row, column=1, sticky="w", padx=(100,0))
        self.aspect_var = tk.BooleanVar(value=True)
        tk.Checkbutton(root, text="Maintain Aspect", variable=self.aspect_var).grid(row=row, column=2, sticky="w")

        # Transform
        row += 1
        tk.Label(root, text="Transform:").grid(row=row, column=0, sticky="w")
        self.transform_var = tk.StringVar(value="None")
        tk.OptionMenu(root, self.transform_var, "None", "Rotate 90", "Rotate 180", "Rotate 270", "Flip Horizontal", "Flip Vertical", "Mirror").grid(row=row, column=1, sticky="w")

        # Filters
        row += 1
        tk.Label(root, text="Filters:").grid(row=row, column=0, sticky="w")
        self.blur_var = tk.BooleanVar()
        self.sharpen_var = tk.BooleanVar()
        self.edge_var = tk.BooleanVar()
        self.gray_var = tk.BooleanVar()
        tk.Checkbutton(root, text="Blur", variable=self.blur_var).grid(row=row, column=1, sticky="w")
        tk.Checkbutton(root, text="Sharpen", variable=self.sharpen_var).grid(row=row, column=1, sticky="w", padx=(60,0))
        tk.Checkbutton(root, text="Edge Detect", variable=self.edge_var).grid(row=row, column=1, sticky="w", padx=(140,0))
        tk.Checkbutton(root, text="Grayscale", variable=self.gray_var).grid(row=row, column=2, sticky="w")

        # Adjustments
        row += 1
        tk.Label(root, text="Brightness (0.1-3.0):").grid(row=row, column=0, sticky="w")
        self.bright_var = tk.StringVar(value="1.0")
        tk.Entry(root, textvariable=self.bright_var, width=6).grid(row=row, column=1, sticky="w")
        tk.Label(root, text="Contrast (0.1-3.0):").grid(row=row, column=2, sticky="w")
        self.contrast_var = tk.StringVar(value="1.0")
        tk.Entry(root, textvariable=self.contrast_var, width=6).grid(row=row, column=2, sticky="e")

        # Watermark
        row += 1
        tk.Label(root, text="Watermark Text:").grid(row=row, column=0, sticky="w")
        self.watermark_var = tk.StringVar()
        tk.Entry(root, textvariable=self.watermark_var, width=30).grid(row=row, column=1, sticky="w")
        tk.Label(root, text="Position:").grid(row=row, column=2, sticky="w")
        self.wpos_var = tk.StringVar(value="bottom-right")
        tk.OptionMenu(root, self.wpos_var, "top-left", "top-right", "center", "bottom-left", "bottom-right").grid(row=row, column=2, sticky="e")

        # Format
        row += 1
        tk.Label(root, text="Format:").grid(row=row, column=0, sticky="w")
        self.format_var = tk.StringVar(value="Original")
        tk.OptionMenu(root, self.format_var, "Original", "JPEG", "PNG").grid(row=row, column=1, sticky="w")

        # Buttons
        row += 1
        tk.Button(root, text="Preview", command=self.preview).grid(row=row, column=0)
        tk.Button(root, text="Start", command=self.start).grid(row=row, column=1)

        # Preview area
        row += 1
        self.preview_label = tk.Label(root, text="Preview will appear here.")
        self.preview_label.grid(row=row, column=0, columnspan=3)

        # Instructions
        row += 1
        tk.Label(root, text="Instructions: Choose folders, select options, then click Start to process all images.").grid(row=row, column=0, columnspan=3, sticky="w")

    def browse_input(self):
        path = filedialog.askdirectory()
        if path:
            self.input_var.set(path)

    def browse_output(self):
        path = filedialog.askdirectory()
        if path:
            self.output_var.set(path)

    def _collect_options(self) -> Options:
        def parse_int(s: str) -> Optional[int]:
            s = (s or "").strip()
            return int(s) if s.isdigit() else None
        def parse_float(s: str, default: float) -> float:
            try:
                v = float(s)
                return max(0.1, min(v, 3.0))
            except Exception:
                return default
        return Options(
            resize=self.resize_var.get(),
            width=parse_int(self.width_var.get()),
            height=parse_int(self.height_var.get()),
            maintain_aspect=self.aspect_var.get(),
            transform=self.transform_var.get(),
            blur=self.blur_var.get(),
            sharpen=self.sharpen_var.get(),
            edge=self.edge_var.get(),
            brightness=parse_float(self.bright_var.get(), 1.0),
            contrast=parse_float(self.contrast_var.get(), 1.0),
            grayscale=self.gray_var.get(),
            watermark_text=self.watermark_var.get(),
            watermark_pos=self.wpos_var.get(),
            target_format=self.format_var.get(),
        )

    def _first_image(self, folder: str) -> Optional[str]:
        if not os.path.isdir(folder):
            return None
        for name in os.listdir(folder):
            path = os.path.join(folder, name)
            if os.path.isfile(path) and is_image_file(path):
                return path
        return None

    def preview(self):
        in_dir = self.input_var.get()
        p = self._first_image(in_dir)
        if not p:
            messagebox.showerror("Error", "No image found in input folder.")
            return
        img = process_image(p, self._collect_options())
        if img is None:
            messagebox.showerror("Error", "Failed to process preview image.")
            return
        # Show small preview
        preview = ImageOps.contain(img, (300, 300))
        self._tk_preview = ImageTk.PhotoImage(preview)
        self.preview_label.configure(image=self._tk_preview, text="")

    def start(self):
        in_dir = self.input_var.get()
        out_dir = self.output_var.get()
        if not os.path.isdir(in_dir):
            messagebox.showerror("Error", "Please select a valid input folder.")
            return
        if not os.path.isdir(out_dir):
            messagebox.showerror("Error", "Please select a valid output folder.")
            return
        files = [os.path.join(in_dir, f) for f in os.listdir(in_dir) if is_image_file(os.path.join(in_dir, f))]
        if not files:
            messagebox.showinfo("Info", "No supported images in input folder.")
            return
        opts = self._collect_options()
        ok = 0
        for f in files:
            img = process_image(f, opts)
            if img is None:
                continue
            try:
                save_output(img, f, out_dir, opts.target_format)
                ok += 1
            except Exception:
                continue
        messagebox.showinfo("Done", f"Processed {ok} of {len(files)} images.")


def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    main()
