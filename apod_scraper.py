from utils import save_image_data, HEADERS
import time
import requests
from bs4 import BeautifulSoup
import re
import datetime
import os

def scrape_apod_images(days_to_scrape=7, force_redownload=False):
    """
    Scrape NASA's Astronomy Picture of the Day
    
    Args:
        days_to_scrape: Number of recent days to scrape (default: 7)
        force_redownload: Whether to re-download existing images
    """
    print("Scraping NASA Astronomy Picture of the Day...")
    
    BASE_URL = "https://apod.nasa.gov/apod/"
    CURRENT_URL = f"{BASE_URL}astropix.html"
    
    # Create a list to store the URLs we need to scrape
    # Start with today's APOD
    urls_to_scrape = [CURRENT_URL]
    
    # Get additional days if requested
    if days_to_scrape > 1:
        # We'll need to find the archive links or construct them
        # APOD archive follows a pattern: ap + YYMMDD + .html
        today = datetime.datetime.now()
        
        for i in range(1, days_to_scrape):
            past_date = today - datetime.timedelta(days=i)
            # Format: apYYMMDD.html
            archive_url = f"{BASE_URL}ap{past_date.strftime('%y%m%d')}.html"
            urls_to_scrape.append(archive_url)
    
    # Process each URL
    downloaded_count = 0
    
    for url in urls_to_scrape:
        try:
            print(f"Fetching APOD from {url}")
            response = requests.get(url, headers=HEADERS)
            
            if response.status_code != 200:
                print(f"Failed to access {url}: {response.status_code}")
                continue
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Extract the date from the URL
            date_match = re.search(r"ap(\d{6})\.html", url)
            date_str = "Today" if url == CURRENT_URL else (
                f"20{date_match.group(1)[:2]}-{date_match.group(1)[2:4]}-{date_match.group(1)[4:]}" 
                if date_match else "Unknown Date"
            )
            
            # Find the title - usually the first center tag with b tag inside
            title_tag = soup.select_one("center b")
            title = title_tag.text.strip() if title_tag else "Astronomy Picture of the Day"
            
            # Find the image - it's usually the first img tag after the title
            # or within the first few elements
            img_tag = None
            
            # First try to find it after the title tag's parent
            if title_tag:
                center_tag = title_tag.parent
                if center_tag:
                    # Try the next centers
                    next_center = center_tag.find_next("center")
                    if next_center:
                        img_tag = next_center.find("img")
            
            # If we didn't find it, look more broadly
            if not img_tag:
                img_tags = soup.find_all("img")
                # Most likely the first or second img tag
                img_tag = img_tags[0] if img_tags else None
            
            # Get the image URL
            if img_tag and img_tag.get("src"):
                img_url = img_tag.get("src")
                # Make sure it's an absolute URL
                if not img_url.startswith("http"):
                    img_url = BASE_URL + img_url
            else:
                # If no image found, skip this day
                print(f"No image found for {date_str}")
                continue
            
            # Find the explanation - usually in a tag following "Explanation:" text
            # First look for the explanation heading
            explanation_text = None
            
            # Try to find the explanation text
            # Look for b tag with "Explanation:" text
            exp_heading = soup.find("b", string=re.compile(r"Explanation:"))
            
            if exp_heading:
                # The explanation often follows this heading in the same parent element
                parent = exp_heading.parent
                if parent:
                    # The explanation text might be directly in the parent or in sibling elements
                    explanation_text = parent.get_text().replace("Explanation:", "", 1).strip()
            
            # If we didn't find it with the above approach, try another method
            if not explanation_text:
                # Try finding a paragraph with substantial text
                paragraphs = soup.find_all("p")
                for p in paragraphs:
                    p_text = p.get_text().strip()
                    # A real explanation will be substantial text
                    if len(p_text) > 100:
                        explanation_text = p_text
                        break
            
            # If still not found, look for any substantial text block
            if not explanation_text:
                # Last resort - get text from the body and do some cleanup
                body_text = soup.body.get_text() if soup.body else ""
                # Try to extract the main text content
                lines = [line.strip() for line in body_text.split("\n") if line.strip()]
                for line in lines:
                    if len(line) > 100 and "Explanation:" not in line:
                        explanation_text = line
                        break
            
            if not explanation_text:
                explanation_text = "No explanation available."
            
            # Find the credit - usually after the explanation
            credit_text = ""
            credit_tag = soup.find(string=re.compile(r"Credit:"))
            if credit_tag:
                # Try to get the full credit line
                credit_parent = credit_tag.parent
                if credit_parent:
                    credit_text = credit_parent.get_text().strip()
                else:
                    credit_text = credit_tag.strip()
            
            # Combine description with credit
            description = f"Date: {date_str}\n\n{explanation_text}"
            if credit_text:
                description += f"\n\nCredit: {credit_text}"
            
            # Get a unique title with date to avoid overwrites between days
            unique_title = f"APOD {date_str} - {title}"
            
            # Save the image
            print(f"Processing APOD image: {unique_title}")
            if save_image_data("NASA_APOD", unique_title, img_url, description, "apod_images", force_redownload):
                downloaded_count += 1
                
            # Be nice to the server
            time.sleep(1)
            
        except Exception as e:
            print(f"Error processing APOD for {url}: {e}")
            continue
    
    print(f"APOD scraping complete - downloaded {downloaded_count} images")
    return downloaded_count > 0 