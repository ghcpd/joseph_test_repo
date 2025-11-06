#!/usr/bin/env python3
"""
Automated Image Processing Program with GUI

This application provides a graphical user interface for batch processing images
with various transformations including resize, filters, rotations, and more.

Author: Automated by GitHub Copilot
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import threading
from processing_functions import batch_process_images, is_image_file


class ImageProcessorGUI:
    """Main GUI application for image processing."""
    
    def __init__(self, root):
        """Initialize the GUI application."""
        self.root = root
        self.root.title("Automated Image Processor")
        self.root.geometry("800x900")
        self.root.resizable(True, True)
        
        # Variables for folder paths
        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        
        # Variables for processing options
        self.setup_processing_variables()
        
        # Create the GUI
        self.create_widgets()
        
        # Preview image variables
        self.preview_image = None
        self.preview_photo = None
    
    def setup_processing_variables(self):
        """Initialize all processing option variables."""
        # Resize options
        self.resize_enabled = tk.BooleanVar()
        self.resize_width = tk.IntVar(value=800)
        self.resize_height = tk.IntVar(value=600)
        self.maintain_aspect = tk.BooleanVar(value=True)
        
        # Rotation/Flip options
        self.rotate_enabled = tk.BooleanVar()
        self.rotate_angle = tk.DoubleVar(value=0)
        self.flip_enabled = tk.BooleanVar()
        self.flip_direction = tk.StringVar(value="horizontal")
        
        # Filter options
        self.blur_enabled = tk.BooleanVar()
        self.blur_radius = tk.DoubleVar(value=2.0)
        self.sharpen_enabled = tk.BooleanVar()
        self.edge_detection_enabled = tk.BooleanVar()
        
        # Adjustment options
        self.brightness_enabled = tk.BooleanVar()
        self.brightness_factor = tk.DoubleVar(value=1.0)
        self.contrast_enabled = tk.BooleanVar()
        self.contrast_factor = tk.DoubleVar(value=1.0)
        self.grayscale_enabled = tk.BooleanVar()
        
        # Watermark options
        self.watermark_enabled = tk.BooleanVar()
        self.watermark_text = tk.StringVar(value="Watermark")
        
        # Format conversion options
        self.format_conversion_enabled = tk.BooleanVar()
        self.target_format = tk.StringVar(value="JPEG")
    
    def create_widgets(self):
        """Create and arrange all GUI widgets."""
        # Create main frame with scrollbar
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="Automated Image Processor", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Instructions
        instructions = ttk.Label(main_frame, 
                                text="Select input and output folders, choose processing options, then click Process Images",
                                font=("Arial", 10))
        instructions.pack(pady=(0, 20))
        
        # Folder selection section
        self.create_folder_selection(main_frame)
        
        # Processing options in a scrollable frame
        self.create_processing_options(main_frame)
        
        # Preview section
        self.create_preview_section(main_frame)
        
        # Process button and progress
        self.create_process_section(main_frame)
    
    def create_folder_selection(self, parent):
        """Create folder selection widgets."""
        folder_frame = ttk.LabelFrame(parent, text="Folder Selection", padding=10)
        folder_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Input folder
        ttk.Label(folder_frame, text="Input Folder:").grid(row=0, column=0, sticky=tk.W, pady=2)
        input_frame = ttk.Frame(folder_frame)
        input_frame.grid(row=0, column=1, columnspan=2, sticky=tk.EW, padx=(10, 0), pady=2)
        
        ttk.Entry(input_frame, textvariable=self.input_folder, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(input_frame, text="Browse", command=self.browse_input_folder).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Output folder
        ttk.Label(folder_frame, text="Output Folder:").grid(row=1, column=0, sticky=tk.W, pady=2)
        output_frame = ttk.Frame(folder_frame)
        output_frame.grid(row=1, column=1, columnspan=2, sticky=tk.EW, padx=(10, 0), pady=2)
        
        ttk.Entry(output_frame, textvariable=self.output_folder, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(output_frame, text="Browse", command=self.browse_output_folder).pack(side=tk.RIGHT, padx=(5, 0))
        
        folder_frame.columnconfigure(1, weight=1)
    
    def create_processing_options(self, parent):
        """Create processing options widgets in a scrollable frame."""
        # Create scrollable frame
        canvas = tk.Canvas(parent, height=300)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Processing options frame
        options_frame = ttk.LabelFrame(scrollable_frame, text="Processing Options", padding=10)
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        row = 0
        
        # Resize options
        ttk.Checkbutton(options_frame, text="Resize", variable=self.resize_enabled).grid(row=row, column=0, sticky=tk.W)
        resize_frame = ttk.Frame(options_frame)
        resize_frame.grid(row=row, column=1, columnspan=3, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(resize_frame, text="Width:").pack(side=tk.LEFT)
        ttk.Entry(resize_frame, textvariable=self.resize_width, width=8).pack(side=tk.LEFT, padx=(5, 10))
        ttk.Label(resize_frame, text="Height:").pack(side=tk.LEFT)
        ttk.Entry(resize_frame, textvariable=self.resize_height, width=8).pack(side=tk.LEFT, padx=(5, 10))
        ttk.Checkbutton(resize_frame, text="Maintain Aspect Ratio", variable=self.maintain_aspect).pack(side=tk.LEFT, padx=(10, 0))
        row += 1
        
        # Rotation options
        ttk.Checkbutton(options_frame, text="Rotate", variable=self.rotate_enabled).grid(row=row, column=0, sticky=tk.W)
        rotation_frame = ttk.Frame(options_frame)
        rotation_frame.grid(row=row, column=1, columnspan=3, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(rotation_frame, text="Angle (degrees):").pack(side=tk.LEFT)
        ttk.Entry(rotation_frame, textvariable=self.rotate_angle, width=8).pack(side=tk.LEFT, padx=(5, 0))
        row += 1
        
        # Flip options
        ttk.Checkbutton(options_frame, text="Flip", variable=self.flip_enabled).grid(row=row, column=0, sticky=tk.W)
        flip_frame = ttk.Frame(options_frame)
        flip_frame.grid(row=row, column=1, columnspan=3, sticky=tk.W, padx=(10, 0))
        
        ttk.Radiobutton(flip_frame, text="Horizontal", variable=self.flip_direction, value="horizontal").pack(side=tk.LEFT)
        ttk.Radiobutton(flip_frame, text="Vertical", variable=self.flip_direction, value="vertical").pack(side=tk.LEFT, padx=(10, 0))
        row += 1
        
        # Filter options
        ttk.Separator(options_frame, orient='horizontal').grid(row=row, column=0, columnspan=4, sticky=tk.EW, pady=10)
        row += 1
        
        ttk.Checkbutton(options_frame, text="Blur", variable=self.blur_enabled).grid(row=row, column=0, sticky=tk.W)
        blur_frame = ttk.Frame(options_frame)
        blur_frame.grid(row=row, column=1, columnspan=3, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(blur_frame, text="Radius:").pack(side=tk.LEFT)
        ttk.Entry(blur_frame, textvariable=self.blur_radius, width=8).pack(side=tk.LEFT, padx=(5, 0))
        row += 1
        
        ttk.Checkbutton(options_frame, text="Sharpen", variable=self.sharpen_enabled).grid(row=row, column=0, sticky=tk.W)
        row += 1
        
        ttk.Checkbutton(options_frame, text="Edge Detection", variable=self.edge_detection_enabled).grid(row=row, column=0, sticky=tk.W)
        row += 1
        
        # Adjustment options
        ttk.Separator(options_frame, orient='horizontal').grid(row=row, column=0, columnspan=4, sticky=tk.EW, pady=10)
        row += 1
        
        ttk.Checkbutton(options_frame, text="Adjust Brightness", variable=self.brightness_enabled).grid(row=row, column=0, sticky=tk.W)
        brightness_frame = ttk.Frame(options_frame)
        brightness_frame.grid(row=row, column=1, columnspan=3, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(brightness_frame, text="Factor (0.5=darker, 1.0=normal, 2.0=brighter):").pack(side=tk.LEFT)
        ttk.Entry(brightness_frame, textvariable=self.brightness_factor, width=8).pack(side=tk.LEFT, padx=(5, 0))
        row += 1
        
        ttk.Checkbutton(options_frame, text="Adjust Contrast", variable=self.contrast_enabled).grid(row=row, column=0, sticky=tk.W)
        contrast_frame = ttk.Frame(options_frame)
        contrast_frame.grid(row=row, column=1, columnspan=3, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(contrast_frame, text="Factor (0.5=less, 1.0=normal, 2.0=more):").pack(side=tk.LEFT)
        ttk.Entry(contrast_frame, textvariable=self.contrast_factor, width=8).pack(side=tk.LEFT, padx=(5, 0))
        row += 1
        
        ttk.Checkbutton(options_frame, text="Convert to Grayscale", variable=self.grayscale_enabled).grid(row=row, column=0, sticky=tk.W)
        row += 1
        
        # Watermark options
        ttk.Separator(options_frame, orient='horizontal').grid(row=row, column=0, columnspan=4, sticky=tk.EW, pady=10)
        row += 1
        
        ttk.Checkbutton(options_frame, text="Add Watermark", variable=self.watermark_enabled).grid(row=row, column=0, sticky=tk.W)
        watermark_frame = ttk.Frame(options_frame)
        watermark_frame.grid(row=row, column=1, columnspan=3, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(watermark_frame, text="Text:").pack(side=tk.LEFT)
        ttk.Entry(watermark_frame, textvariable=self.watermark_text, width=20).pack(side=tk.LEFT, padx=(5, 0))
        row += 1
        
        # Format conversion options
        ttk.Separator(options_frame, orient='horizontal').grid(row=row, column=0, columnspan=4, sticky=tk.EW, pady=10)
        row += 1
        
        ttk.Checkbutton(options_frame, text="Convert Format", variable=self.format_conversion_enabled).grid(row=row, column=0, sticky=tk.W)
        format_frame = ttk.Frame(options_frame)
        format_frame.grid(row=row, column=1, columnspan=3, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(format_frame, text="Target Format:").pack(side=tk.LEFT)
        format_combo = ttk.Combobox(format_frame, textvariable=self.target_format, width=10, state="readonly")
        format_combo['values'] = ("JPEG", "PNG")
        format_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # Configure grid weights
        options_frame.columnconfigure(1, weight=1)
    
    def create_preview_section(self, parent):
        """Create preview section widgets."""
        preview_frame = ttk.LabelFrame(parent, text="Preview (Select an image from input folder)", padding=10)
        preview_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Preview controls
        control_frame = ttk.Frame(preview_frame)
        control_frame.pack(fill=tk.X)
        
        ttk.Button(control_frame, text="Load Preview", command=self.load_preview).pack(side=tk.LEFT)
        ttk.Button(control_frame, text="Generate Preview", command=self.generate_preview).pack(side=tk.LEFT, padx=(10, 0))
        
        # Preview image label
        self.preview_label = ttk.Label(preview_frame, text="No preview loaded")
        self.preview_label.pack(pady=10)
    
    def create_process_section(self, parent):
        """Create process button and progress widgets."""
        process_frame = ttk.Frame(parent)
        process_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Process button
        self.process_button = ttk.Button(process_frame, text="Process Images", 
                                       command=self.start_processing, style="Accent.TButton")
        self.process_button.pack(pady=(0, 10))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(process_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        # Status text
        self.status_text = scrolledtext.ScrolledText(process_frame, height=6, wrap=tk.WORD)
        self.status_text.pack(fill=tk.X)
    
    def browse_input_folder(self):
        """Browse for input folder."""
        folder = filedialog.askdirectory(title="Select Input Folder")
        if folder:
            self.input_folder.set(folder)
            self.log_status(f"Input folder set to: {folder}")
    
    def browse_output_folder(self):
        """Browse for output folder."""
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder.set(folder)
            self.log_status(f"Output folder set to: {folder}")
    
    def load_preview(self):
        """Load an image for preview."""
        input_dir = self.input_folder.get()
        if not input_dir or not os.path.exists(input_dir):
            messagebox.showerror("Error", "Please select a valid input folder first.")
            return
        
        # Get image files from input directory
        image_files = [f for f in os.listdir(input_dir) if is_image_file(f)]
        if not image_files:
            messagebox.showwarning("Warning", "No supported image files found in input folder.")
            return
        
        # Let user select an image file
        filetypes = [
            ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.gif"),
            ("All files", "*.*")
        ]
        
        image_path = filedialog.askopenfilename(
            title="Select image for preview",
            initialdir=input_dir,
            filetypes=filetypes
        )
        
        if image_path:
            try:
                # Load and display the image
                image = Image.open(image_path)
                # Resize for preview while maintaining aspect ratio
                image.thumbnail((300, 300), Image.Resampling.LANCZOS)
                
                self.preview_image = image
                self.preview_photo = ImageTk.PhotoImage(image)
                
                self.preview_label.configure(image=self.preview_photo, text="")
                self.log_status(f"Preview loaded: {os.path.basename(image_path)}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {str(e)}")
    
    def generate_preview(self):
        """Generate a preview of the processed image."""
        if not self.preview_image:
            messagebox.showwarning("Warning", "Please load a preview image first.")
            return
        
        try:
            # Create operations dictionary
            operations = self.get_operations_dict()
            
            # Apply operations to preview image
            from processing_functions import (resize_image, rotate_image, flip_image, apply_blur,
                                            apply_sharpen, apply_edge_detection, adjust_brightness,
                                            adjust_contrast, convert_to_grayscale, add_watermark,
                                            convert_format)
            
            processed_image = self.preview_image.copy()
            
            # Apply operations in order
            if operations.get('resize', {}).get('enabled', False):
                resize_ops = operations['resize']
                processed_image = resize_image(
                    processed_image,
                    resize_ops.get('width', processed_image.width),
                    resize_ops.get('height', processed_image.height),
                    resize_ops.get('maintain_aspect', True)
                )
            
            if operations.get('rotate', {}).get('enabled', False):
                angle = operations['rotate'].get('angle', 0)
                if angle != 0:
                    processed_image = rotate_image(processed_image, angle)
            
            if operations.get('flip', {}).get('enabled', False):
                direction = operations['flip'].get('direction', 'horizontal')
                processed_image = flip_image(processed_image, direction)
            
            if operations.get('blur', {}).get('enabled', False):
                radius = operations['blur'].get('radius', 2.0)
                processed_image = apply_blur(processed_image, radius)
            
            if operations.get('sharpen', {}).get('enabled', False):
                processed_image = apply_sharpen(processed_image)
            
            if operations.get('edge_detection', {}).get('enabled', False):
                processed_image = apply_edge_detection(processed_image)
            
            if operations.get('brightness', {}).get('enabled', False):
                factor = operations['brightness'].get('factor', 1.0)
                processed_image = adjust_brightness(processed_image, factor)
            
            if operations.get('contrast', {}).get('enabled', False):
                factor = operations['contrast'].get('factor', 1.0)
                processed_image = adjust_contrast(processed_image, factor)
            
            if operations.get('grayscale', {}).get('enabled', False):
                processed_image = convert_to_grayscale(processed_image)
            
            if operations.get('watermark', {}).get('enabled', False):
                watermark_ops = operations['watermark']
                text = watermark_ops.get('text', 'Watermark')
                processed_image = add_watermark(processed_image, text)
            
            if operations.get('format_conversion', {}).get('enabled', False):
                target_format = operations['format_conversion'].get('format', 'JPEG')
                processed_image = convert_format(processed_image, target_format)
            
            # Resize for preview display
            processed_image.thumbnail((300, 300), Image.Resampling.LANCZOS)
            
            # Update preview
            self.preview_photo = ImageTk.PhotoImage(processed_image)
            self.preview_label.configure(image=self.preview_photo, text="")
            self.log_status("Preview generated with current settings.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate preview: {str(e)}")
    
    def get_operations_dict(self):
        """Build operations dictionary from GUI settings."""
        operations = {}
        
        # Resize
        if self.resize_enabled.get():
            operations['resize'] = {
                'enabled': True,
                'width': self.resize_width.get(),
                'height': self.resize_height.get(),
                'maintain_aspect': self.maintain_aspect.get()
            }
        
        # Rotation
        if self.rotate_enabled.get():
            operations['rotate'] = {
                'enabled': True,
                'angle': self.rotate_angle.get()
            }
        
        # Flip
        if self.flip_enabled.get():
            operations['flip'] = {
                'enabled': True,
                'direction': self.flip_direction.get()
            }
        
        # Filters
        if self.blur_enabled.get():
            operations['blur'] = {
                'enabled': True,
                'radius': self.blur_radius.get()
            }
        
        if self.sharpen_enabled.get():
            operations['sharpen'] = {'enabled': True}
        
        if self.edge_detection_enabled.get():
            operations['edge_detection'] = {'enabled': True}
        
        # Adjustments
        if self.brightness_enabled.get():
            operations['brightness'] = {
                'enabled': True,
                'factor': self.brightness_factor.get()
            }
        
        if self.contrast_enabled.get():
            operations['contrast'] = {
                'enabled': True,
                'factor': self.contrast_factor.get()
            }
        
        if self.grayscale_enabled.get():
            operations['grayscale'] = {'enabled': True}
        
        # Watermark
        if self.watermark_enabled.get():
            operations['watermark'] = {
                'enabled': True,
                'text': self.watermark_text.get()
            }
        
        # Format conversion
        if self.format_conversion_enabled.get():
            operations['format_conversion'] = {
                'enabled': True,
                'format': self.target_format.get()
            }
        
        return operations
    
    def start_processing(self):
        """Start the batch processing in a separate thread."""
        # Validate inputs
        if not self.input_folder.get() or not os.path.exists(self.input_folder.get()):
            messagebox.showerror("Error", "Please select a valid input folder.")
            return
        
        if not self.output_folder.get():
            messagebox.showerror("Error", "Please select an output folder.")
            return
        
        # Check if any operations are selected
        operations = self.get_operations_dict()
        if not operations:
            messagebox.showwarning("Warning", "Please select at least one processing option.")
            return
        
        # Disable process button and start processing
        self.process_button.configure(state="disabled")
        self.progress_var.set(0)
        self.status_text.delete(1.0, tk.END)
        
        # Start processing in a separate thread
        thread = threading.Thread(target=self.process_images, args=(operations,))
        thread.daemon = True
        thread.start()
    
    def process_images(self, operations):
        """Process images (runs in separate thread)."""
        try:
            input_dir = self.input_folder.get()
            output_dir = self.output_folder.get()
            
            self.log_status("Starting batch processing...")
            self.log_status(f"Input folder: {input_dir}")
            self.log_status(f"Output folder: {output_dir}")
            self.log_status(f"Operations: {list(operations.keys())}")
            
            def progress_callback(current, total):
                """Update progress bar."""
                progress = (current / total) * 100 if total > 0 else 0
                self.root.after(0, lambda: self.progress_var.set(progress))
                self.root.after(0, lambda: self.log_status(f"Processing image {current}/{total}"))
            
            # Process images
            successful, total = batch_process_images(input_dir, output_dir, operations, progress_callback)
            
            # Update UI on main thread
            self.root.after(0, lambda: self.processing_complete(successful, total))
            
        except Exception as e:
            self.root.after(0, lambda: self.processing_error(str(e)))
    
    def processing_complete(self, successful, total):
        """Handle processing completion."""
        self.progress_var.set(100)
        self.process_button.configure(state="normal")
        
        message = f"Processing complete! {successful}/{total} images processed successfully."
        self.log_status(message)
        
        if successful < total:
            messagebox.showwarning("Processing Complete", 
                                 f"Processing finished with some errors.\n{successful}/{total} images processed successfully.")
        else:
            messagebox.showinfo("Processing Complete", 
                              f"All {successful} images processed successfully!")
    
    def processing_error(self, error_message):
        """Handle processing error."""
        self.process_button.configure(state="normal")
        self.log_status(f"Error during processing: {error_message}")
        messagebox.showerror("Processing Error", f"An error occurred during processing:\n{error_message}")
    
    def log_status(self, message):
        """Log a status message."""
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()


def main():
    """Main application entry point."""
    # Create and configure root window
    root = tk.Tk()
    
    # Set up the application
    app = ImageProcessorGUI(root)
    
    # Set default folders to input and output directories
    current_dir = os.path.dirname(os.path.abspath(__file__))
    default_input = os.path.join(current_dir, "input")
    default_output = os.path.join(current_dir, "output")
    
    if os.path.exists(default_input):
        app.input_folder.set(default_input)
    if os.path.exists(default_output):
        app.output_folder.set(default_output)
    
    # Initial status message
    app.log_status("Image Processor GUI started.")
    app.log_status("Instructions:")
    app.log_status("1. Select input and output folders")
    app.log_status("2. Choose processing options")
    app.log_status("3. Optionally load and preview an image")
    app.log_status("4. Click 'Process Images' to start batch processing")
    app.log_status("Supported formats: JPG, JPEG, PNG, BMP, TIFF, GIF")
    
    # Start the GUI event loop
    root.mainloop()


if __name__ == "__main__":
    main()