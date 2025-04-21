import requests
from bs4 import BeautifulSoup

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
                
        # Print overall page structure for analysis        
        print(f"\nPage structure overview:")
        for tag in soup.find_all(["div", "section", "main"])[:5]:
            if "class" in tag.attrs:
                print(f"{tag.name} - classes: {tag.get('class')}") 