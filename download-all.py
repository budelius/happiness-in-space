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

def create_image_with_text_overlay(img_data, description, max_width=80):
    # Load image from binary data
    img = Image.open(io.BytesIO(img_data))
    
    # Create a semi-transparent overlay
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Add a semi-transparent background for text
    draw.rectangle([(0, img.height - img.height/3), (img.width, img.height)], fill=(0, 0, 0, 180))
    
    # Try to use a system font, fall back to default if not available
    try:
        font = ImageFont.truetype("Arial", 20)
    except IOError:
        font = ImageFont.load_default()
    
    # Wrap text to fit the image width
    wrapper = textwrap.TextWrapper(width=max_width)
    wrapped_text = wrapper.fill(description[:500] + ("..." if len(description) > 500 else ""))
    
    # Add text to the overlay
    padding = 20
    y_position = img.height - img.height/3 + padding
    for line in wrapped_text.split('\n'):
        draw.text((padding, y_position), line, font=font, fill=(255, 255, 255, 255))
        y_position += 24  # Line height
    
    # Convert images to RGBA if they aren't already
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Combine the image with the overlay
    result = Image.alpha_composite(img, overlay)
    return result

def save_image_data(source, title, image_url, description, outdir):
    os.makedirs(outdir, exist_ok=True)
    safe_title = sanitize_filename(title)
    image_ext = os.path.splitext(image_url)[-1].split("?")[0]
    if not image_ext:
        image_ext = ".jpg"  # Default extension if none found
    
    img_path = os.path.join(outdir, f"{safe_title}{image_ext}")
    overlay_path = os.path.join(outdir, f"{safe_title}_overlay{image_ext}")
    txt_path = os.path.join(outdir, f"{safe_title}.txt")

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
    except Exception as e:
        print(f"Failed to save {title}: {e}")

### ---- ESA ---- ###
def scrape_esa_images():
    print("Scraping ESA...")
    BASE_URL = "https://www.esa.int"
    START_URL = f"{BASE_URL}/Applications/Observing_the_Earth/Highlights/Image_of_the_Day"
    seen_links = set()
    current_url = START_URL

    def get_soup(url):
        return BeautifulSoup(requests.get(url, headers=HEADERS).content, "html.parser")

    while current_url:
        soup = get_soup(current_url)
        # The class structure has changed from "teaser" to "feature-item"
        feature_items = soup.find_all("div", class_="feature-item")

        for item in feature_items:
            # Find the anchor link which is inside the feature-item
            a_tag = item.find("a", class_="cta popup")
            if not a_tag or "href" not in a_tag.attrs:
                continue

            href = a_tag["href"]
            full_url = BASE_URL + href if not href.startswith("http") else href
            if full_url in seen_links:
                continue
            seen_links.add(full_url)

            try:
                detail = get_soup(full_url)
                title = detail.find("h1").text.strip()
                # Find description in the modal__tab-description div
                desc_div = detail.find("div", class_="modal__tab-description")
                desc = desc_div.text.strip() if desc_div else "No description available"
                
                # Find the main image src - it's often a direct image with a pillars.jpg format
                img_element = detail.find("meta", property="og:image")
                if img_element and "content" in img_element.attrs:
                    img_url = img_element["content"]
                else:
                    # Fallback to find the main image
                    img_div = detail.find("img", alt=title)
                    if img_div and "src" in img_div.attrs:
                        img_url = img_div["src"]
                        if not img_url.startswith("http"):
                            img_url = BASE_URL + img_url
                    else:
                        continue  # Skip if we can't find an image
                
                save_image_data("ESA", title, img_url, desc, "esa_images")
                time.sleep(1)
            except Exception as e:
                print(f"ESA error: {e}")

        # Find the next page link - ESA uses rel="next" now
        next_link = soup.find("a", class_="next") or soup.find("a", rel="next")
        if next_link and "href" in next_link.attrs:
            current_url = BASE_URL + next_link["href"] if not next_link["href"].startswith("http") else next_link["href"]
        else:
            break

### ---- NASA ---- ###
def scrape_nasa_images():
    print("Scraping NASA...")
    BASE_URL = "https://www.nasa.gov"
    START_URL = "https://www.nasa.gov/multimedia/imagegallery/iotd.html"
    visited = set()
    current_url = START_URL

    def get_soup(url):
        return BeautifulSoup(requests.get(url).content, "html.parser")

    while current_url:
        soup = get_soup(current_url)
        links = soup.select("div.item_list .item a")
        for a in links:
            href = a["href"]
            full_url = href if href.startswith("http") else BASE_URL + href
            if full_url in visited:
                continue
            visited.add(full_url)

            try:
                page = get_soup(full_url)
                title = page.find("h1").text.strip()
                desc = page.find("div", class_="wysiwyg_content").text.strip()
                img = page.find("figure", class_="lede").find("img")["src"]
                img_url = img if img.startswith("http") else BASE_URL + img
                save_image_data("NASA", title, img_url, desc, "nasa_images")
                time.sleep(1)
            except Exception as e:
                print(f"NASA error: {e}")

        next_btn = soup.find("a", class_="pagination-next")
        current_url = BASE_URL + next_btn["href"] if next_btn else None

### ---- JAXA ---- ###
def scrape_jaxa_images():
    print("Scraping JAXA...")
    BASE_URL = "https://earth.jaxa.jp"
    START_URL = f"{BASE_URL}/en/earthview/"

    soup = BeautifulSoup(requests.get(START_URL).content, "html.parser")
    links = [BASE_URL + a["href"] for a in soup.select("section.earthview-list a") if "href" in a.attrs]

    for url in links:
        try:
            detail = BeautifulSoup(requests.get(url).content, "html.parser")
            title = detail.find("h1").text.strip()
            desc = detail.find("div", class_="earthview-summary").text.strip()
            img = detail.find("div", class_="earthview-image").find("img")["src"]
            img_url = BASE_URL + img if not img.startswith("http") else img
            save_image_data("JAXA", title, img_url, desc, "jaxa_images")
            time.sleep(1)
        except Exception as e:
            print(f"JAXA error: {e}")

### ---- Main ---- ###
def setup_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Source", "Title", "Image URL", "Description", "Saved Image Path"])

if __name__ == "__main__":
    setup_csv()
    scrape_esa_images()
    scrape_nasa_images()
    scrape_jaxa_images()
