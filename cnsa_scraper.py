from utils import save_image_data, HEADERS
import requests
from bs4 import BeautifulSoup
import time

def scrape_cnsa_images(force_redownload=False, recreate_overlays=False):
    if recreate_overlays:
        print("CNSA: Recreate overlays mode - skipping image scraping")
        return
        
    print("Scraping CNSA...")
    BASE_URL = "https://www.cnsa.gov.cn/english"
    START_URL = f"{BASE_URL}"
    
    try:
        # Get the main page
        response = requests.get(START_URL, headers=HEADERS)
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Look for image galleries or news sections with images
        # CNSA website structure might change, so we need to inspect the current structure
        # and adjust the scraping logic accordingly
        
        # Try to find news items or featured content sections
        news_items = soup.find_all("div", class_="new") or soup.find_all("div", class_="news-list")
        
        if not news_items:
            # Fallback to find other potential containers
            news_items = soup.find_all("div", class_="list") or soup.find_all("ul", class_="list")
        
        for item in news_items:
            links = item.find_all("a")
            for link in links:
                if not link.get("href"):
                    continue
                    
                href = link["href"]
                if not href.startswith("http"):
                    # Make relative URLs absolute
                    if href.startswith("/"):
                        full_url = f"https://www.cnsa.gov.cn{href}"
                    else:
                        full_url = f"{BASE_URL}/{href}"
                else:
                    full_url = href
                
                try:
                    # Get the detail page
                    detail_response = requests.get(full_url, headers=HEADERS)
                    detail_soup = BeautifulSoup(detail_response.content, "html.parser")
                    
                    # Try to find the title
                    title_elem = detail_soup.find("h1") or detail_soup.find("div", class_="title")
                    if not title_elem:
                        continue
                        
                    title = title_elem.text.strip()
                    
                    # Try to find the content/description
                    content_elem = detail_soup.find("div", class_="TRS_Editor") or detail_soup.find("div", class_="content")
                    desc = content_elem.text.strip() if content_elem else "No description available"
                    
                    # Find images in the content
                    images = content_elem.find_all("img") if content_elem else []
                    
                    if not images:
                        # Try to find images elsewhere on the page
                        images = detail_soup.find_all("img", class_="img-responsive") or detail_soup.find_all("img")
                    
                    # Process and save each image found
                    for i, img in enumerate(images):
                        if not img.get("src"):
                            continue
                            
                        img_url = img["src"]
                        if not img_url.startswith("http"):
                            # Make relative URLs absolute
                            if img_url.startswith("/"):
                                img_url = f"https://www.cnsa.gov.cn{img_url}"
                            else:
                                img_url = f"{BASE_URL}/{img_url}"
                        
                        # Add a suffix for multiple images from the same article
                        img_title = title
                        if i > 0:
                            img_title = f"{title} ({i+1})"
                            
                        save_image_data("CNSA", img_title, img_url, desc, "cnsa_images", force_redownload, recreate_overlays)
                        time.sleep(1)
                        
                except Exception as e:
                    print(f"CNSA detail error: {e}")
                
                # Don't overload the server
                time.sleep(2)
                
    except Exception as e:
        print(f"CNSA error: {e}") 