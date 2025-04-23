from utils import save_image_data, HEADERS
import time
import requests
import traceback

def scrape_nasa_images(force_redownload=False):
    print("Scraping NASA...")
    
    # NASA now has a dedicated Images API we can use instead of scraping
    API_URL = "https://images-api.nasa.gov/search"
    
    try:
        # Get NASA images from their Images API
        # Search for space images and sort by recent ones first
        params = {
            "q": "earth OR planet OR space OR moon OR mars",  # Simplified query
            "media_type": "image",
            "year_start": "2020",  # Recent images for better quality
            "page_size": 20        # Get a reasonable number of images
        }
        
        print("Fetching images from NASA API...")
        response = requests.get(API_URL, params=params)
        if response.status_code != 200:
            print(f"Failed to access NASA API: {response.status_code}")
            return
        
        data = response.json()
        
        # Debug info
        if not isinstance(data, dict) or "collection" not in data:
            print(f"Unexpected API response format: {type(data)}")
            return
            
        items = data["collection"]["items"]
        print(f"Found {len(items)} NASA images")
        
        for item in items:
            try:
                # Extract metadata
                if "data" not in item or not item["data"]:
                    print("Missing data in item")
                    continue
                    
                metadata = item["data"][0]
                title = metadata.get("title", "Untitled NASA Image")
                desc = metadata.get("description", "No description available")
                
                # If the description is too short, add the keywords
                if len(desc) < 50 and "keywords" in metadata:
                    keywords = metadata.get("keywords", [])
                    if isinstance(keywords, list):
                        desc += " | Keywords: " + ", ".join(keywords)
                
                # Get the image URL - we need to find the image link in the links array
                if "links" not in item or not item["links"]:
                    print(f"No links found for {title}")
                    continue
                
                # First try to find a large image
                img_url = None
                for link in item["links"]:
                    if "href" not in link:
                        continue
                        
                    if "render" in link and link["render"] == "image":
                        img_url = link["href"]
                        # If we find a large version, prefer it
                        if "large" in link["href"]:
                            img_url = link["href"]
                            break
                
                # If we didn't find a render:image link, fall back to first image link
                if not img_url and len(item["links"]) > 0:
                    img_url = item["links"][0].get("href")
                
                if not img_url:
                    print(f"No image URL found for {title}")
                    continue
                
                # Sometimes NASA API returns http URLs, convert to https
                if img_url.startswith("http://"):
                    img_url = "https://" + img_url[7:]
                
                print(f"Processing NASA image: {title} - {img_url}")
                save_image_data("NASA", title, img_url, desc, "nasa_images", force_redownload)
                time.sleep(1)  # Be respectful with rate limiting
                
            except Exception as e:
                print(f"Error processing NASA image: {e}")
                traceback.print_exc()
                
        print("NASA scraping complete")
    except Exception as e:
        print(f"NASA scraping error: {e}")
        traceback.print_exc() 