import os
import csv
import time
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
import io
import textwrap

HEADERS = {"User-Agent": "Mozilla/5.0"}
CSV_FILE = "./data/image_catalog.csv"

def sanitize_filename(name):
    return "".join(c if c.isalnum() or c in " _-" else "_" for c in name)[:100]

def create_image_with_text_overlay(img_data, description, max_width=40):
    # Load image from binary data
    img = Image.open(io.BytesIO(img_data))
    
    # Create a semi-transparent overlay
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Add a semi-transparent background for text that's half width and half height
    # Center it horizontally, keep at bottom
    overlay_width = img.width // 2
    overlay_height = img.height // 6  # Half of previous height (was img.height/3)
    left = (img.width - overlay_width) // 2  # Center horizontally
    top = img.height - overlay_height
    right = left + overlay_width
    bottom = img.height
    
    draw.rectangle([(left, top), (right, bottom)], fill=(0, 0, 0, 180))
    
    # Try to use a system font, fall back to default if not available
    try:
        font = ImageFont.truetype("Arial", 20)
    except IOError:
        font = ImageFont.load_default()
    
    # Wrap text to fit the reduced overlay width 
    wrapper = textwrap.TextWrapper(width=max_width)
    wrapped_text = wrapper.fill(description[:250] + ("..." if len(description) > 250 else ""))
    
    # Add text to the overlay
    padding = 20
    y_position = top + padding
    for line in wrapped_text.split('\n'):
        # Center text in overlay
        text_width = draw.textlength(line, font=font) if hasattr(draw, "textlength") else font.getsize(line)[0]
        x_position = left + (overlay_width - text_width) // 2
        draw.text((x_position, y_position), line, font=font, fill=(255, 255, 255, 255))
        y_position += 24  # Line height
    
    # Convert images to RGBA if they aren't already
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Combine the image with the overlay
    result = Image.alpha_composite(img, overlay)
    return result

def save_image_data(source, title, image_url, description, outdir, force_redownload=False):
    os.makedirs(outdir, exist_ok=True)
    safe_title = sanitize_filename(title)
    image_ext = os.path.splitext(image_url)[-1].split("?")[0]
    if not image_ext:
        image_ext = ".jpg"  # Default extension if none found
    
    img_path = os.path.join(outdir, f"{safe_title}{image_ext}")
    overlay_path = os.path.join(outdir, f"{safe_title}_overlay{image_ext}")
    txt_path = os.path.join(outdir, f"{safe_title}.txt")

    # Check if image already exists
    if os.path.exists(img_path) and not force_redownload:
        print(f"Skipping (already exists): {safe_title}")
        return False

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

def setup_csv():
    os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Source", "Title", "Image URL", "Description", "Saved Image Path"]) 