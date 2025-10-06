# Automated Image Processing Program with GUI

A Python application with a graphical user interface for batch processing images with various transformations and filters.

## Features

- **Folder Selection**: Choose input and output directories
- **Batch Processing**: Process all images in a folder automatically
- **Multiple Processing Options**:
  - **Resize**: Adjust image dimensions with optional aspect ratio preservation
  - **Rotate**: Rotate images by any angle
  - **Flip/Mirror**: Horizontal or vertical flipping
  - **Filters**: Blur, Sharpen, Edge Detection
  - **Adjustments**: Brightness, Contrast, Grayscale conversion
  - **Watermark**: Add custom text overlays
  - **Format Conversion**: Convert between JPEG and PNG
- **Preview**: Load and preview images with applied transformations
- **Progress Tracking**: Real-time progress updates during batch processing
- **Error Handling**: Graceful handling of unsupported files and errors

## Requirements

- Python 3.x
- Required packages (install with `pip install -r requirements.txt`):
  - Pillow >= 11.0.0
  - numpy >= 1.21.0
  - tkinter (usually included with Python)

## Installation

1. Clone or download this repository
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python image_processor.py
   ```

## Usage

1. **Launch the Application**:
   ```bash
   python image_processor.py
   ```

2. **Select Folders**:
   - Click "Browse" next to "Input Folder" to select the folder containing your original images
   - Click "Browse" next to "Output Folder" to select where processed images will be saved
   - The application automatically sets default `input/` and `output/` folders if they exist

3. **Choose Processing Options**:
   - Check the boxes for the transformations you want to apply
   - Adjust parameters for each option (width/height for resize, angle for rotation, etc.)
   - Multiple options can be selected and will be applied in sequence

4. **Preview (Optional)**:
   - Click "Load Preview" to select an image from your input folder
   - Click "Generate Preview" to see how the image will look with your selected processing options

5. **Process Images**:
   - Click "Process Images" to start batch processing
   - Monitor progress in the progress bar and status log
   - Processed images will be saved in the output folder with "_processed" added to the filename

## Processing Options Details

### Resize
- Set custom width and height
- Option to maintain aspect ratio (recommended)
- Images larger than specified dimensions will be scaled down

### Rotate/Flip
- **Rotate**: Specify angle in degrees (positive = clockwise)
- **Flip**: Choose horizontal or vertical flipping

### Filters
- **Blur**: Gaussian blur with adjustable radius
- **Sharpen**: Enhance image details
- **Edge Detection**: Highlight edges in the image

### Adjustments
- **Brightness**: Factor of 1.0 = no change, >1.0 = brighter, <1.0 = darker
- **Contrast**: Factor of 1.0 = no change, >1.0 = more contrast, <1.0 = less contrast
- **Grayscale**: Convert to black and white

### Watermark
- Add custom text overlay to images
- Text is automatically centered on the image
- Semi-transparent white text for visibility

### Format Conversion
- Convert between JPEG and PNG formats
- Handles transparency appropriately (PNG to JPEG gets white background)

## Supported File Formats

**Input**: JPG, JPEG, PNG, BMP, TIFF, GIF
**Output**: JPG, PNG (based on format conversion setting)

## File Naming

Processed images are saved with the original filename plus "_processed" suffix:
- `photo.jpg` → `photo_processed.jpg`
- `image.png` → `image_processed.png` (or `.jpg` if converting to JPEG)

## Error Handling

The application handles various error conditions gracefully:
- Unsupported file formats are skipped
- Corrupted images are logged and skipped
- Missing folders are reported with helpful error messages
- Progress continues even if individual images fail to process

## Directory Structure

```
image_processor/
├── image_processor.py          # Main GUI application
├── processing_functions.py     # Image processing utilities
├── requirements.txt           # Python dependencies
├── README.md                 # This file
├── input/                   # Default input folder
└── output/                  # Default output folder
```

## Tips

- **Performance**: Processing large numbers of high-resolution images may take time
- **Preview**: Use the preview feature to test settings before batch processing
- **Backup**: Keep backups of original images before processing
- **Memory**: For very large images, consider resizing to reduce memory usage
- **File Names**: Avoid special characters in file names for best compatibility

## Troubleshooting

**Application won't start**: 
- Ensure Python 3.x is installed
- Install required packages: `pip install Pillow numpy`
- On Linux, you may need: `sudo apt install python3-tk`

**Images not processing**:
- Check that input folder contains supported image files
- Ensure output folder is writable
- Check the status log for specific error messages

**Preview not working**:
- Ensure input folder is selected and contains images
- Try loading a different image file
- Check that the image file is not corrupted

## License

This project is open source and available under the MIT License.