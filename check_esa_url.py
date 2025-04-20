import requests
from bs4 import BeautifulSoup
import sys

def check_url(url):
    print(f"Checking URL: {url}")
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Check for article elements
            articles = soup.find_all("article", class_="teaser")
            print(f"Found {len(articles)} articles with class='teaser'")
            
            # Try other common article classes
            other_articles = soup.find_all("article")
            print(f"Found {len(other_articles)} generic articles")
            
            # Look for any items/cards
            cards = soup.find_all(class_=lambda c: c and ("card" in c or "item" in c))
            print(f"Found {len(cards)} elements with 'card' or 'item' in their class")
            
            # Check for image elements
            images = soup.find_all("div", class_="image")
            print(f"Found {len(images)} div elements with class='image'")
            
            # Print a few element types to understand structure
            print("\nPage structure elements:")
            for tag_name in ["header", "main", "section", "nav", "footer"]:
                elements = soup.find_all(tag_name)
                if elements:
                    print(f"Found {len(elements)} {tag_name} elements")
            
            # Print the first few headings to understand page content
            print("\nPage headings:")
            for i, heading in enumerate(soup.find_all(["h1", "h2", "h3"])[:5]):
                print(f"Heading {i+1}: {heading.text.strip()}")
                
            # Look at link structure
            print("\nChecking pagination:")
            pagination = soup.find_all(class_=lambda c: c and "pagination" in c)
            if pagination:
                print(f"Found {len(pagination)} pagination elements")
                # Check for next links
                next_links = soup.find_all("a", class_="next")
                if next_links:
                    print(f"Found {len(next_links)} 'next' links")
                    for link in next_links:
                        print(f"  Next link: {link.get('href', 'No href')}")
            else:
                print("No pagination elements found")
                
            return True
        else:
            print(f"Failed to access URL. Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

# URLs to check
urls = [
    "https://www.esa.int/Applications/Observing_the_Earth/Highlights/Image_of_the_Day",
    "https://www.esa.int/Applications/Observing_the_Earth/Copernicus/Earth_from_Space",
    "https://www.esa.int/ESA_Multimedia/Sets/Earth_observation_image_of_the_week"
]

for url in urls:
    print("\n" + "="*80)
    check_url(url)
    print("="*80) 