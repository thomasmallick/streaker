import cv2
import numpy as np
import os
import logging
from typing import Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('streak_removal.log'),
        logging.StreamHandler()
    ]
)

def detect_streaks(gray_image: np.ndarray) -> Tuple[bool, Optional[np.ndarray]]:
    """
    Detect vertical streaks in a grayscale image.
    Returns (has_streaks, mask) where mask contains the detected streaks.
    """
    height, width = gray_image.shape
    
    # Detect vertical edges using Sobel - much more sensitive
    edges = cv2.Sobel(gray_image, cv2.CV_8U, 1, 0, ksize=3)
    _, mask = cv2.threshold(edges, 20, 255, cv2.THRESH_BINARY)  # Lowered threshold

    # Morphological operations to enhance vertical lines
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 10))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    # Find contours to identify line-like structures
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter contours for vertical lines
    filtered_mask = np.zeros_like(gray_image)
    streak_count = 0
    
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = h / max(w, 1)
        
        # Check if it's a vertical line (tall and thin)
        if aspect_ratio > 5 and h > height * 0.1 and w < 10:
            cv2.drawContours(filtered_mask, [contour], -1, 255, -1)
            streak_count += 1
    
    has_streaks = streak_count > 0
    return has_streaks, filtered_mask if has_streaks else None

def remove_streaks(image_path: str, output_path: str) -> bool:
    """
    Remove streaks from an image if they are detected.
    Returns True if streaks were found and removed, False otherwise.
    """
    # Read the image
    img = cv2.imread(image_path)
    if img is None:
        logging.error(f"Failed to read image: {image_path}")
        return False
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Detect streaks
    has_streaks, streak_mask = detect_streaks(gray)
    
    if not has_streaks:
        logging.info(f"No streaks detected in {os.path.basename(image_path)}")
        return False
    
    # Apply inpainting with subtle settings
    inpaint_radius = 2
    inpainted = cv2.inpaint(img, streak_mask, inpaint_radius, cv2.INPAINT_TELEA)
    
    # Save the result
    cv2.imwrite(output_path, inpainted)
    
    logging.info(f"✓ FIXED: {os.path.basename(image_path)} - Streaks removed and saved to {output_path}")
    return True

# Process all images in a folder
def batch_process_images(input_folder: str, output_folder: str) -> None:
    """
    Process all images in a folder, only fixing those with detected streaks.
    """
    if not os.path.exists(input_folder):
        logging.error(f"Input folder does not exist: {input_folder}")
        return
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        logging.info(f"Created output folder: {output_folder}")
    
    image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif')
    processed_count = 0
    fixed_count = 0
    
    logging.info(f"Starting batch processing of folder: {input_folder}")
    
    for filename in os.listdir(input_folder):
        if filename.lower().endswith(image_extensions):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)
            
            processed_count += 1
            
            if remove_streaks(input_path, output_path):
                fixed_count += 1
    
    logging.info(f"\n=== BATCH PROCESSING COMPLETE ===")
    logging.info(f"Total images processed: {processed_count}")
    logging.info(f"Images with streaks fixed: {fixed_count}")
    logging.info(f"Images without streaks: {processed_count - fixed_count}")
    
    if fixed_count > 0:
        logging.info(f"\n=== FIXED IMAGES ===")
        for filename in os.listdir(input_folder):
            if filename.lower().endswith(image_extensions):
                input_path = os.path.join(input_folder, filename)
                output_path = os.path.join(output_folder, filename)
                
                # Check if output file exists and is newer than input
                if os.path.exists(output_path):
                    img = cv2.imread(input_path)
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    has_streaks, _ = detect_streaks(gray)
                    if has_streaks:
                        logging.info(f"• {filename}")

def main():
    """
    Main function with configurable input/output folders.
    """
    # You can modify these paths as needed
    input_folder = "../data/input"  # Change to your folder path
    output_folder = "../data/output"
    
    # Alternative: use command line arguments
    # import sys
    # if len(sys.argv) > 1:
    #     input_folder = sys.argv[1]
    # if len(sys.argv) > 2:
    #     output_folder = sys.argv[2]
    
    logging.info("=== STREAK REMOVAL SCRIPT STARTED ===")
    logging.info(f"Input folder: {input_folder}")
    logging.info(f"Output folder: {output_folder}")
    
    batch_process_images(input_folder, output_folder)
    
    logging.info("=== STREAK REMOVAL SCRIPT COMPLETED ===")

if __name__ == "__main__":
    main()
