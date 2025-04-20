import os
import csv
import time
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}
CSV_FILE = "./data/image_catalog.csv"

def sanitize_filename(name):
    return "".join(c if c.isalnum() or c in " _-" else "_" for c in name)[:100]

def save_image_data(source, title, image_url, description, outdir):
    os.makedirs(outdir, exist_ok=True)
    safe_title = sanitize_filename(title)
    image_ext = os.path.splitext(image_url)[-1].split("?")[0]
    img_path = os.path.join(outdir, f"{safe_title}{image_ext}")
    txt_path = os.path.join(outdir, f"{safe_title}.txt")

    try:
        img_data = requests.get(image_url, headers=HEADERS).content
        with open(img_path, 'wb') as f:
            f.write(img_data)

        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(description)

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
        articles = soup.find_all("article", class_="teaser")

        for article in articles:
            href = article.find("a", href=True)["href"]
            full_url = BASE_URL + href if not href.startswith("http") else href
            if full_url in seen_links:
                continue
            seen_links.add(full_url)

            try:
                detail = get_soup(full_url)
                title = detail.find("h1").text.strip()
                desc = detail.find("div", class_="editorial").text.strip()
                img = detail.find("div", class_="image").find("img")["src"]
                img_url = BASE_URL + img if not img.startswith("http") else img
                save_image_data("ESA", title, img_url, desc, "esa_images")
                time.sleep(1)
            except Exception as e:
                print(f"ESA error: {e}")

        next_link = soup.find("a", class_="next")
        if next_link and "href" in next_link.attrs:
            current_url = BASE_URL + next_link["href"]
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
