"""
Image Processing Functions Module

This module contains all the image processing functions used by the GUI application.
Each function handles a specific type of image transformation using Pillow and numpy.
"""

import os
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw, ImageFont
from typing import Optional, Tuple, List


def resize_image(image: Image.Image, width: int, height: int, maintain_aspect: bool = True) -> Image.Image:
    """
    Resize an image to specified dimensions.
    
    Args:
        image: PIL Image object
        width: Target width
        height: Target height
        maintain_aspect: Whether to maintain aspect ratio
    
    Returns:
        Resized PIL Image object
    """
    if maintain_aspect:
        image.thumbnail((width, height), Image.Resampling.LANCZOS)
        return image
    else:
        return image.resize((width, height), Image.Resampling.LANCZOS)


def rotate_image(image: Image.Image, angle: float) -> Image.Image:
    """
    Rotate an image by specified angle.
    
    Args:
        image: PIL Image object
        angle: Rotation angle in degrees
    
    Returns:
        Rotated PIL Image object
    """
    return image.rotate(angle, expand=True, fillcolor='white')


def flip_image(image: Image.Image, direction: str) -> Image.Image:
    """
    Flip an image horizontally or vertically.
    
    Args:
        image: PIL Image object
        direction: 'horizontal' or 'vertical'
    
    Returns:
        Flipped PIL Image object
    """
    if direction.lower() == 'horizontal':
        return image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    elif direction.lower() == 'vertical':
        return image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    else:
        return image


def apply_blur(image: Image.Image, radius: float = 2.0) -> Image.Image:
    """
    Apply Gaussian blur to an image.
    
    Args:
        image: PIL Image object
        radius: Blur radius
    
    Returns:
        Blurred PIL Image object
    """
    return image.filter(ImageFilter.GaussianBlur(radius=radius))


def apply_sharpen(image: Image.Image) -> Image.Image:
    """
    Apply sharpening filter to an image.
    
    Args:
        image: PIL Image object
    
    Returns:
        Sharpened PIL Image object
    """
    return image.filter(ImageFilter.SHARPEN)


def apply_edge_detection(image: Image.Image) -> Image.Image:
    """
    Apply edge detection filter to an image.
    
    Args:
        image: PIL Image object
    
    Returns:
        Edge-detected PIL Image object
    """
    return image.filter(ImageFilter.FIND_EDGES)


def adjust_brightness(image: Image.Image, factor: float) -> Image.Image:
    """
    Adjust brightness of an image.
    
    Args:
        image: PIL Image object
        factor: Brightness factor (1.0 = no change, >1.0 = brighter, <1.0 = darker)
    
    Returns:
        Brightness-adjusted PIL Image object
    """
    enhancer = ImageEnhance.Brightness(image)
    return enhancer.enhance(factor)


def adjust_contrast(image: Image.Image, factor: float) -> Image.Image:
    """
    Adjust contrast of an image.
    
    Args:
        image: PIL Image object
        factor: Contrast factor (1.0 = no change, >1.0 = more contrast, <1.0 = less contrast)
    
    Returns:
        Contrast-adjusted PIL Image object
    """
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(factor)


def convert_to_grayscale(image: Image.Image) -> Image.Image:
    """
    Convert an image to grayscale.
    
    Args:
        image: PIL Image object
    
    Returns:
        Grayscale PIL Image object
    """
    return image.convert('L').convert('RGB')


def add_watermark(image: Image.Image, text: str, position: Tuple[int, int] = None, 
                 font_size: int = 36, opacity: int = 128) -> Image.Image:
    """
    Add text watermark to an image.
    
    Args:
        image: PIL Image object
        text: Watermark text
        position: Position tuple (x, y). If None, centers the watermark
        font_size: Font size for the watermark
        opacity: Opacity of the watermark (0-255)
    
    Returns:
        Watermarked PIL Image object
    """
    # Create a copy of the image
    watermarked = image.copy()
    
    # Create a transparent overlay
    overlay = Image.new('RGBA', watermarked.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Try to use a default font, fallback to built-in if not available
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except (OSError, IOError):
        # Use default PIL font
        font = ImageFont.load_default()
    
    # Calculate text size and position
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    if position is None:
        # Center the watermark
        x = (watermarked.width - text_width) // 2
        y = (watermarked.height - text_height) // 2
    else:
        x, y = position
    
    # Draw the text
    draw.text((x, y), text, fill=(255, 255, 255, opacity), font=font)
    
    # Composite the overlay with the original image
    watermarked = Image.alpha_composite(watermarked.convert('RGBA'), overlay)
    return watermarked.convert('RGB')


def convert_format(image: Image.Image, target_format: str) -> Image.Image:
    """
    Convert image format (ensure proper mode for target format).
    
    Args:
        image: PIL Image object
        target_format: Target format ('JPEG' or 'PNG')
    
    Returns:
        Format-converted PIL Image object
    """
    if target_format.upper() == 'JPEG' and image.mode in ('RGBA', 'LA', 'P'):
        # Convert to RGB for JPEG (no transparency support)
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
        return background
    elif target_format.upper() == 'PNG' and image.mode not in ('RGBA', 'RGB', 'L'):
        return image.convert('RGBA')
    
    return image


def get_supported_formats() -> List[str]:
    """
    Get list of supported image formats.
    
    Returns:
        List of supported file extensions
    """
    return ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']


def is_image_file(filepath: str) -> bool:
    """
    Check if a file is a supported image format.
    
    Args:
        filepath: Path to the file
    
    Returns:
        True if the file is a supported image format
    """
    _, ext = os.path.splitext(filepath.lower())
    return ext in get_supported_formats()


def process_image(image_path: str, output_path: str, operations: dict) -> bool:
    """
    Process a single image with specified operations.
    
    Args:
        image_path: Path to input image
        output_path: Path to save processed image
        operations: Dictionary of operations and their parameters
    
    Returns:
        True if processing was successful, False otherwise
    """
    try:
        # Open the image
        image = Image.open(image_path)
        
        # Apply operations in order
        if operations.get('resize', {}).get('enabled', False):
            resize_ops = operations['resize']
            image = resize_image(
                image, 
                resize_ops.get('width', image.width),
                resize_ops.get('height', image.height),
                resize_ops.get('maintain_aspect', True)
            )
        
        if operations.get('rotate', {}).get('enabled', False):
            angle = operations['rotate'].get('angle', 0)
            if angle != 0:
                image = rotate_image(image, angle)
        
        if operations.get('flip', {}).get('enabled', False):
            direction = operations['flip'].get('direction', 'horizontal')
            image = flip_image(image, direction)
        
        if operations.get('blur', {}).get('enabled', False):
            radius = operations['blur'].get('radius', 2.0)
            image = apply_blur(image, radius)
        
        if operations.get('sharpen', {}).get('enabled', False):
            image = apply_sharpen(image)
        
        if operations.get('edge_detection', {}).get('enabled', False):
            image = apply_edge_detection(image)
        
        if operations.get('brightness', {}).get('enabled', False):
            factor = operations['brightness'].get('factor', 1.0)
            image = adjust_brightness(image, factor)
        
        if operations.get('contrast', {}).get('enabled', False):
            factor = operations['contrast'].get('factor', 1.0)
            image = adjust_contrast(image, factor)
        
        if operations.get('grayscale', {}).get('enabled', False):
            image = convert_to_grayscale(image)
        
        if operations.get('watermark', {}).get('enabled', False):
            watermark_ops = operations['watermark']
            text = watermark_ops.get('text', 'Watermark')
            position = watermark_ops.get('position', None)
            image = add_watermark(image, text, position)
        
        if operations.get('format_conversion', {}).get('enabled', False):
            target_format = operations['format_conversion'].get('format', 'JPEG')
            image = convert_format(image, target_format)
        
        # Save the processed image
        image.save(output_path, quality=95)
        return True
        
    except Exception as e:
        print(f"Error processing {image_path}: {str(e)}")
        return False


def batch_process_images(input_folder: str, output_folder: str, operations: dict, 
                        progress_callback=None) -> Tuple[int, int]:
    """
    Batch process all images in a folder.
    
    Args:
        input_folder: Path to input folder
        output_folder: Path to output folder
        operations: Dictionary of operations to apply
        progress_callback: Optional callback function for progress updates
    
    Returns:
        Tuple of (successful_count, total_count)
    """
    if not os.path.exists(input_folder):
        return 0, 0
    
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Get all image files
    image_files = [f for f in os.listdir(input_folder) if is_image_file(f)]
    total_count = len(image_files)
    successful_count = 0
    
    for i, filename in enumerate(image_files):
        input_path = os.path.join(input_folder, filename)
        
        # Generate output filename
        name, ext = os.path.splitext(filename)
        
        # Determine output extension based on format conversion
        if operations.get('format_conversion', {}).get('enabled', False):
            target_format = operations['format_conversion'].get('format', 'JPEG')
            if target_format.upper() == 'PNG':
                ext = '.png'
            else:
                ext = '.jpg'
        
        output_filename = f"{name}_processed{ext}"
        output_path = os.path.join(output_folder, output_filename)
        
        # Process the image
        if process_image(input_path, output_path, operations):
            successful_count += 1
        
        # Update progress
        if progress_callback:
            progress_callback(i + 1, total_count)
    
    return successful_count, total_count