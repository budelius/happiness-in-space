import os
import csv
import time
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
import io
import textwrap
import glob

HEADERS = {"User-Agent": "Mozilla/5.0"}
CSV_FILE = "./data/image_catalog.csv"

def sanitize_filename(name):
    return "".join(c if c.isalnum() or c in " _-" else "_" for c in name)[:100]

def create_image_with_text_overlay(img_data, description, max_width=60):
    # Load image from binary data
    img = Image.open(io.BytesIO(img_data))
    
    # Create a semi-transparent overlay
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Try to use a system font, fall back to default if not available
    try:
        font = ImageFont.truetype("Arial", 20)
    except IOError:
        font = ImageFont.load_default()
    
    # Wrap text to fit the width - increased max_width for longer lines
    wrapper = textwrap.TextWrapper(width=max_width)
    
    # Increase character limit from 250 to 800 characters
    description_limit = 1600
    wrapped_text = wrapper.fill(description[:description_limit] + ("..." if len(description) > description_limit else ""))
    
    # Count the number of lines to determine overlay height
    lines = wrapped_text.split('\n')
    num_lines = len(lines)
    
    # Calculate overlay dimensions - adjust height based on number of lines
    line_height = 24
    padding = 20
    required_height = (num_lines * line_height) + (padding * 2)
    
    # Make sure overlay doesn't exceed 1/4 of the image height (reduced from 1/3)
    max_overlay_height = img.height // 4
    overlay_height = min(required_height, max_overlay_height)
    
    # For width, use 3/4 of the image width to allow for more text per line
    overlay_width = int(img.width * 0.75)
    
    # Position - shifted more to the right
    left = int(img.width * 0.15)  # Start at 15% from left edge
    top = 0
    right = left + overlay_width
    bottom = top + overlay_height
    
    # Create the background rectangle
    draw.rectangle([(left, top), (right, bottom)], fill=(0, 0, 0, 180))
    
    # Add text to the overlay
    y_position = top + padding
    for line in lines:
        # Position text with padding from the left edge of overlay
        x_position = left + padding
        draw.text((x_position, y_position), line, font=font, fill=(255, 255, 255, 255))
        y_position += line_height
        
        # Stop drawing text if we go beyond the overlay height
        if y_position > bottom - padding:
            break
    
    # Convert images to RGBA if they aren't already
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Combine the image with the overlay
    result = Image.alpha_composite(img, overlay)
    return result

def save_image_data(source, title, image_url, description, outdir, force_redownload=False, recreate_overlays=False):
    os.makedirs(outdir, exist_ok=True)
    safe_title = sanitize_filename(title)
    image_ext = os.path.splitext(image_url)[-1].split("?")[0]
    if not image_ext:
        image_ext = ".jpg"  # Default extension if none found
    
    img_path = os.path.join(outdir, f"{safe_title}{image_ext}")
    overlay_path = os.path.join(outdir, f"{safe_title}_overlay{image_ext}")
    txt_path = os.path.join(outdir, f"{safe_title}.txt")

    # Check if we're in recreate_overlays mode and the original image exists
    if recreate_overlays and os.path.exists(img_path):
        try:
            # Read the original image instead of downloading it
            with open(img_path, 'rb') as f:
                img_data = f.read()
                
            # Read description from text file if it exists, otherwise use provided description
            if os.path.exists(txt_path):
                with open(txt_path, 'r', encoding='utf-8') as f:
                    description = f.read()
            
            # Create and save the new overlay image
            overlay_img = create_image_with_text_overlay(img_data, description)
            overlay_img = overlay_img.convert('RGB')  # Convert to RGB for saving jpg
            overlay_img.save(overlay_path)
            print(f"Recreated overlay for: {safe_title}")
            return True
            
        except Exception as e:
            print(f"Failed to recreate overlay for {title}: {e}")
            return False
    
    # Skip if image exists and we're not forcing redownload or just recreating overlays
    if os.path.exists(img_path) and not force_redownload and not recreate_overlays:
        print(f"Skipping (already exists): {safe_title}")
        return False

    # Standard download and save process
    if not recreate_overlays:
        try:
            img_data = requests.get(image_url, headers=HEADERS).content
            
            # Save original image
            with open(img_path, 'wb') as f:
                f.write(img_data)
                
            # Create and save image with text overlay
            try:
                overlay_img = create_image_with_text_overlay(img_data, description)
                overlay_img = overlay_img.convert('RGB')  # Convert to RGB for saving jpg
                overlay_img.save(overlay_path)
            except Exception as e:
                print(f"Failed to create overlay for {title}: {e}")

            # Save description as text file
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(description)

            # Record in CSV
            with open(CSV_FILE, "a", encoding="utf-8", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([source, title, image_url, description, img_path])

            print(f"Saved: {safe_title}")
            return True
        except Exception as e:
            print(f"Failed to save {title}: {e}")
            return False

def regenerate_all_overlays(directory):
    """
    Regenerate overlay images for all original images in a directory
    
    Args:
        directory: Directory containing images to process
    
    Returns:
        Number of overlays regenerated
    """
    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        return 0
        
    print(f"Regenerating overlays in {directory}...")
    
    # Find all images that don't have '_overlay' in the filename
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif']
    original_images = []
    
    for ext in image_extensions:
        pattern = os.path.join(directory, ext)
        original_images.extend([f for f in glob.glob(pattern) if '_overlay' not in f])
    
    print(f"Found {len(original_images)} original images")
    regenerated_count = 0
    
    for img_path in original_images:
        try:
            # Get base filename
            filename = os.path.basename(img_path)
            base_name, ext = os.path.splitext(filename)
            
            # Paths for related files
            overlay_path = os.path.join(directory, f"{base_name}_overlay{ext}")
            txt_path = os.path.join(directory, f"{base_name}.txt")
            
            # Read the original image
            with open(img_path, 'rb') as f:
                img_data = f.read()
            
            # Read description from text file if it exists
            description = "No description available."
            if os.path.exists(txt_path):
                with open(txt_path, 'r', encoding='utf-8') as f:
                    description = f.read()
            
            # Create and save new overlay
            overlay_img = create_image_with_text_overlay(img_data, description)
            overlay_img = overlay_img.convert('RGB')  # Convert to RGB for saving jpg
            overlay_img.save(overlay_path)
            
            regenerated_count += 1
            if regenerated_count % 10 == 0:
                print(f"Regenerated {regenerated_count} overlays so far...")
                
        except Exception as e:
            print(f"Error regenerating overlay for {img_path}: {e}")
    
    print(f"Regenerated {regenerated_count} overlays in {directory}")
    return regenerated_count

def setup_csv():
    os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Source", "Title", "Image URL", "Description", "Saved Image Path"]) 