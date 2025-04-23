from utils import save_image_data, HEADERS
import time
import requests
from bs4 import BeautifulSoup

def scrape_esa_images(force_redownload=False):
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
                
                save_image_data("ESA", title, img_url, desc, "esa_images", force_redownload)
                time.sleep(1)
            except Exception as e:
                print(f"ESA error: {e}")

        # Find the next page link - ESA uses rel="next" now
        next_link = soup.find("a", class_="next") or soup.find("a", rel="next")
        if next_link and "href" in next_link.attrs:
            current_url = BASE_URL + next_link["href"] if not next_link["href"].startswith("http") else next_link["href"]
        else:
            break 