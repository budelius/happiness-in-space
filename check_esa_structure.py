import requests
from bs4 import BeautifulSoup
import json

HEADERS = {"User-Agent": "Mozilla/5.0"}
BASE_URL = "https://www.esa.int"
START_URL = f"{BASE_URL}/ESA_Multimedia/Sets/Technology_image_of_the_week"

# Try different possible URLs
urls_to_try = [
    f"{BASE_URL}/Highlights/Image_of_the_Week", # Original URL in the script
    f"{BASE_URL}/ESA_Multimedia/Sets/Technology_image_of_the_week",
    f"{BASE_URL}/ESA_Multimedia/Images/Sets",
    f"{BASE_URL}/Highlights/Week_in_images"
]

for url in urls_to_try:
    print(f"\nTrying URL: {url}")
    response = requests.get(url, headers=HEADERS)
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Try different possible selectors for articles
        selectors = [
            "article.teaser",  # Original selector in the script
            "article",
            ".card",
            ".result-item",
            ".grid--result-item",
            ".gallery-item"
        ]
        
        for selector in selectors:
            items = soup.select(selector)
            print(f"\nSelector '{selector}' found {len(items)} items")
            if items:
                print(f"First item structure:")
                print(items[0].prettify()[:300] + "...\n")
                
        # Print overall page structure overview        
        print(f"\nPage structure overview:")
        for tag in soup.find_all(["div", "section", "main"])[:5]:
            if "class" in tag.attrs:
                print(f"{tag.name} - classes: {tag.get('class')}")

def check_esa_structure():
    print("Checking ESA Image of the Day structure...")
    url = "https://www.esa.int/Applications/Observing_the_Earth/Highlights/Image_of_the_Day"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Inspect the structure
        print(f"Status code: {response.status_code}")
        
        # Find all potential article containers
        print("\nPotential article containers:")
        for tag in ["article", "div", "section", "li"]:
            elements = soup.find_all(tag, class_=lambda c: c is not None)
            for element in elements:
                if element.find("a") and (element.find("img") or element.find("h2") or element.find("h3")):
                    print(f"Found potential article container: <{tag} class='{element.get('class')}'>")
                    
                    # Check for title
                    title_elem = element.find(["h1", "h2", "h3", "h4"]) 
                    if title_elem:
                        print(f"  - Title: {title_elem.text.strip()}")
                    
                    # Check for links
                    links = element.find_all("a", href=True)
                    if links:
                        print(f"  - Found {len(links)} links:")
                        for i, link in enumerate(links[:2]):  # Show first 2 links
                            print(f"    Link {i+1}: {link.get('href', 'No href')}")
                    
                    # Check for images
                    images = element.find_all("img", src=True)
                    if images:
                        print(f"  - Found {len(images)} images:")
                        for i, img in enumerate(images[:2]):  # Show first 2 images
                            print(f"    Image {i+1}: {img.get('src', 'No src')}")
                    print()
        
        # Now let's find one article and see what we can extract
        print("\nDetailed inspection of first article:")
        articles = soup.select("div.grid--result-item")
        if articles:
            first_article = articles[0]
            print("First article HTML structure:")
            print(first_article.prettify()[:500] + "...\n") # Print first 500 chars
            
            # Attempt to extract key elements
            title = first_article.find(["h2", "h3"])
            link = first_article.find("a", href=True)
            img = first_article.find("img", src=True)
            
            if title:
                print(f"Title: {title.text.strip()}")
            if link:
                print(f"Link: {link['href']}")
            if img:
                print(f"Image: {img['src']}")
                
            print("\nProposed extraction logic:")
            print("""
            BASE_URL = "https://www.esa.int"
            articles = soup.select("div.grid--result-item")
            
            for article in articles:
                title = article.find(["h2", "h3"]).text.strip()
                link_elem = article.find("a", href=True)
                href = link_elem["href"]
                full_url = BASE_URL + href if not href.startswith("http") else href
                
                # Now fetch the detail page
                detail_soup = BeautifulSoup(requests.get(full_url, headers=HEADERS).content, "html.parser")
                # Extract details from the detail page
                # ...
            """)
        else:
            print("No articles found with div.grid--result-item selector")
        
        # Print overall page info summary
        print("\nPage Summary:")
        print(f"Title: {soup.title.text if soup.title else 'No title'}")
        print(f"Links: {len(soup.find_all('a', href=True))}")
        print(f"Images: {len(soup.find_all('img', src=True))}")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_esa_structure() 