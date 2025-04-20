import requests
from bs4 import BeautifulSoup

def analyze_esa_page():
    """Analyze the ESA Image of the Day page structure"""
    url = "https://www.esa.int/Applications/Observing_the_Earth/Highlights/Image_of_the_Day"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code != 200:
            print("Failed to access the URL")
            return
            
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Look for articles or similar containers
        print("\n=== Article Containers ===")
        container_selectors = [
            "article.teaser",  # Original selector in script
            "div.grid--result-item",  # Observed in HTML inspection
            "div.card",
            "li.result-item"
        ]
        
        for selector in container_selectors:
            containers = soup.select(selector)
            print(f"Selector '{selector}': {len(containers)} items found")
            
            if containers:
                # Print the structure of the first container
                print("First container structure:")
                print(containers[0].prettify()[:300] + "...\n")
        
        # Look for common elements
        print("\n=== Common Elements ===")
        common_elements = [
            ("Title Elements", ["h1", "h2", "h3"]),
            ("Link Elements", ["a[href]"]),
            ("Image Elements", ["img[src]", "div.image"]),
            ("Date Elements", ["time", "span.date"])
        ]
        
        for name, selectors in common_elements:
            print(f"{name}:")
            for selector in selectors:
                elements = soup.select(selector)
                print(f"  '{selector}': {len(elements)} found")
                if elements and len(elements) < 5:
                    for i, el in enumerate(elements):
                        if selector == "a[href]":
                            print(f"    {i+1}. {el.get('href', 'No href')}")
                        elif selector == "img[src]":
                            print(f"    {i+1}. {el.get('src', 'No src')}")
                        else:
                            print(f"    {i+1}. {el.text.strip()[:50]}")
        
        # Examine one full item in detail
        print("\n=== Detailed Item Analysis ===")
        # Try with grid items first
        items = soup.select("div.grid--result-item")
        if not items:
            items = soup.select("article")
        
        if items:
            item = items[0]
            print("Item HTML:")
            print(item.prettify()[:500] + "...")
            
            # Extract important elements
            title_elem = item.select_one("h2, h3, h4")
            link_elem = item.select_one("a[href]")
            img_elem = item.select_one("img[src]")
            
            print("\nExtracted elements:")
            if title_elem:
                print(f"Title: {title_elem.text.strip()}")
            if link_elem:
                print(f"Link: {link_elem.get('href')}")
            if img_elem:
                print(f"Image: {img_elem.get('src')}")
        
            # Suggest updated scraping logic
            print("\nSuggested scraping logic:")
            if "grid--result-item" in str(item.get("class", [])):
                print("""
                # Updated scraping logic
                BASE_URL = "https://www.esa.int"
                items = soup.select("div.grid--result-item")
                
                for item in items:
                    title_elem = item.select_one("h2, h3")
                    link_elem = item.select_one("a[href]")
                    
                    if title_elem and link_elem:
                        title = title_elem.text.strip()
                        href = link_elem.get("href")
                        full_url = BASE_URL + href if not href.startswith("http") else href
                        
                        # Visit the detail page
                        detail_soup = BeautifulSoup(requests.get(full_url, headers=HEADERS).content, "html.parser")
                        
                        # Extract detail page elements
                        desc_elem = detail_soup.select_one("div.editorial")
                        img_elem = detail_soup.select_one("div.image img")
                        
                        if desc_elem and img_elem:
                            desc = desc_elem.text.strip()
                            img_url = img_elem.get("src")
                            img_url = BASE_URL + img_url if not img_url.startswith("http") else img_url
                            
                            # Save the data
                            save_image_data("ESA", title, img_url, desc, "esa_images")
                """)
            else:
                print("Alternative item structure found - need to adjust extraction logic")
        else:
            print("No suitable items found on the page")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_esa_page() 