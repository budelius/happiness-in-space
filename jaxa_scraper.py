from utils import save_image_data, HEADERS
import time
import requests
from bs4 import BeautifulSoup
import re

def scrape_jaxa_images(force_redownload=False):
    print("Scraping JAXA...")
    
    # JAXA has several Earth observation data sources
    # Let's try to get images from multiple JAXA sources
    jaxa_sources = [
        # JASMES SGLI Near Real-Time Monitor has good images of Earth
        {
            "base_url": "https://www.eorc.jaxa.jp",
            "start_url": "https://www.eorc.jaxa.jp/JASMES/SGLI_NRT/index.html",
            "name": "JASMES SGLI NRT"
        },
        # GCOM-C (SHIKISAI) Image Gallery
        {
            "base_url": "https://www.eorc.jaxa.jp",
            "start_url": "https://suzaku.eorc.jaxa.jp/GCOM_C/gallery/index.html",
            "name": "GCOM-C Gallery"
        },
        # JAXA Earth Observation Research Portal
        {
            "base_url": "https://earth.jaxa.jp",
            "start_url": "https://earth.jaxa.jp/en/earthview/",
            "name": "Earth-graphy"
        }
    ]
    
    downloaded_count = 0
    max_images = 20  # Set a limit on total images to download
    
    for source in jaxa_sources:
        if downloaded_count >= max_images:
            break
            
        print(f"Trying to get images from {source['name']}...")
        
        try:
            response = requests.get(source["start_url"], headers=HEADERS)
            if response.status_code != 200:
                print(f"Failed to access {source['name']}: {response.status_code}")
                continue
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Different approaches depending on the source
            if source["name"] == "JASMES SGLI NRT":
                # Look for image areas or data visualizations
                area_divs = soup.select(".areaImages img") or soup.select(".area img") or soup.select("img[src*='area']")
                
                if area_divs:
                    print(f"Found {len(area_divs)} area images in {source['name']}")
                    
                    for img in area_divs[:5]:  # Limit to 5 per source
                        if downloaded_count >= max_images:
                            break
                            
                        try:
                            img_url = img.get("src")
                            if not img_url:
                                continue
                                
                            if not img_url.startswith("http"):
                                img_url = source["base_url"] + ('' if img_url.startswith('/') else '/') + img_url
                            
                            # Try to get title from alt text
                            title = img.get("alt") or f"JAXA SGLI Area {downloaded_count+1}"
                            desc = "JAXA SGLI satellite Earth observation image."
                            
                            print(f"Processing JAXA image: {title}")
                            # Only increment downloaded_count if the image was actually saved
                            if save_image_data("JAXA", title, img_url, desc, "jaxa_images", force_redownload):
                                downloaded_count += 1
                            time.sleep(1)
                            
                        except Exception as e:
                            print(f"Error processing JASMES image: {e}")
                else:
                    # Try the fallback method - look for links that lead to image pages
                    all_links = soup.find_all("a")
                    image_links = []
                    
                    for link in all_links:
                        href = link.get("href", "")
                        # Look for JavaScript opens that contain image URLs
                        onclick = link.get("onclick", "")
                        if href and "SGLI_NRT/sgli_nrt.htm" in href:
                            image_links.append(link)
                        elif onclick and "openNewWin" in onclick and ".cgi" in onclick:
                            image_links.append(link)
                            
                    if image_links:
                        print(f"Found {len(image_links)} potential SGLI links/buttons")
                        
                        for link in image_links[:5]:
                            if downloaded_count >= max_images:
                                break
                                
                            # If we find a link to a visualization page, follow it
                            href = link.get("href", "")
                            onclick = link.get("onclick", "")
                            
                            # Extract URL from JavaScript if needed
                            if onclick and not href:
                                url_match = re.search(r"openNewWin\('([^']+)'", onclick)
                                if url_match:
                                    href = url_match.group(1)
                            
                            if href:
                                if not href.startswith("http"):
                                    href = source["base_url"] + ('' if href.startswith('/') else '/') + href
                                
                                try:
                                    print(f"Following link to visualization: {href}")
                                    viz_response = requests.get(href, headers=HEADERS)
                                    if viz_response.status_code == 200:
                                        viz_soup = BeautifulSoup(viz_response.content, "html.parser")
                                        
                                        # Look for the main image in the visualization
                                        viz_imgs = viz_soup.select("img.mainImg") or viz_soup.select("img#mainImage") or viz_soup.select("img[src*='data']")
                                        
                                        if viz_imgs:
                                            img_url = viz_imgs[0].get("src")
                                            if img_url and not img_url.startswith("http"):
                                                img_url = source["base_url"] + ('' if img_url.startswith('/') else '/') + img_url
                                                
                                            title = link.get_text().strip() if link else viz_soup.select_one("h1, h2").text.strip() if viz_soup.select_one("h1, h2") else f"JAXA SGLI Visualization {downloaded_count+1}"
                                            desc = "JAXA SGLI satellite Earth observation visualization."
                                            
                                            print(f"Processing JAXA image: {title}")
                                            if save_image_data("JAXA", title, img_url, desc, "jaxa_images", force_redownload):
                                                downloaded_count += 1
                                            time.sleep(1)
                                except Exception as e:
                                    print(f"Error following visualization link: {e}")
            
            elif source["name"] == "GCOM-C Gallery":
                # GCOM-C Gallery has a different structure
                gallery_items = soup.select(".gallery_item") or soup.select(".item") or soup.select("a[href*='gallery']")
                
                if gallery_items:
                    print(f"Found {len(gallery_items)} gallery items in {source['name']}")
                    
                    for item in gallery_items[:5]:  # Limit to 5 per source
                        if downloaded_count >= max_images:
                            break
                            
                        try:
                            # Get the link to the image
                            link = item if item.name == "a" else item.find("a")
                            if not link or not link.get("href"):
                                continue
                                
                            href = link.get("href")
                            if not href.startswith("http"):
                                href = source["base_url"] + ('' if href.startswith('/') else '/') + href
                            
                            # Check if there's an image in the gallery item
                            img = item.find("img")
                            if img and img.get("src"):
                                img_url = img.get("src")
                                if not img_url.startswith("http"):
                                    img_url = source["base_url"] + ('' if img_url.startswith('/') else '/') + img_url
                                
                                # Check if it's a thumbnail and we need the full image
                                if "thumb" in img_url or "small" in img_url:
                                    # Follow link to get full image
                                    detail_response = requests.get(href, headers=HEADERS)
                                    if detail_response.status_code == 200:
                                        detail_soup = BeautifulSoup(detail_response.content, "html.parser")
                                        full_img = detail_soup.select_one("img.fullsize") or detail_soup.select_one("img.mainImage") or detail_soup.select_one("div.image-container img")
                                        
                                        if full_img and full_img.get("src"):
                                            img_url = full_img.get("src")
                                            if not img_url.startswith("http"):
                                                img_url = source["base_url"] + ('' if img_url.startswith('/') else '/') + img_url
                                
                                title = img.get("alt") or link.get_text().strip() or f"JAXA GCOM-C Image {downloaded_count+1}"
                                desc = "JAXA GCOM-C (SHIKISAI) satellite Earth observation image."
                                
                                print(f"Processing JAXA image: {title}")
                                if save_image_data("JAXA", title, img_url, desc, "jaxa_images", force_redownload):
                                    downloaded_count += 1
                                time.sleep(1)
                            else:
                                # No image in gallery item, follow link to detail page
                                detail_response = requests.get(href, headers=HEADERS)
                                if detail_response.status_code == 200:
                                    detail_soup = BeautifulSoup(detail_response.content, "html.parser")
                                    
                                    # Find the image in the detail page
                                    detail_img = detail_soup.select_one("img.fullsize") or detail_soup.select_one("img.mainImage") or detail_soup.select_one("div.image-container img")
                                    
                                    if detail_img and detail_img.get("src"):
                                        img_url = detail_img.get("src")
                                        if not img_url.startswith("http"):
                                            img_url = source["base_url"] + ('' if img_url.startswith('/') else '/') + img_url
                                        
                                        title = detail_soup.select_one("h1, h2").text.strip() if detail_soup.select_one("h1, h2") else f"JAXA GCOM-C Image {downloaded_count+1}"
                                        desc_elem = detail_soup.select_one("div.description") or detail_soup.select_one("p.content")
                                        desc = desc_elem.text.strip() if desc_elem else "JAXA GCOM-C (SHIKISAI) satellite Earth observation image."
                                        
                                        print(f"Processing JAXA image: {title}")
                                        if save_image_data("JAXA", title, img_url, desc, "jaxa_images", force_redownload):
                                            downloaded_count += 1
                                        time.sleep(1)
                        except Exception as e:
                            print(f"Error processing GCOM-C gallery item: {e}")
            
            elif source["name"] == "Earth-graphy":
                # Earth-graphy has articles with featured images
                articles = soup.select("article") or soup.select(".feature-item") or soup.select(".earthview-list a")
                
                if articles:
                    print(f"Found {len(articles)} articles in {source['name']}")
                    
                    for article in articles[:5]:  # Limit to 5 per source
                        if downloaded_count >= max_images:
                            break
                            
                        try:
                            # Find the link to the article
                            link = article.find("a", class_="cta popup") or article.find("a")
                            if not link or not link.get("href"):
                                continue
                                
                            href = link.get("href")
                            if not href.startswith("http"):
                                href = source["base_url"] + ('' if href.startswith('/') else '/') + href
                            
                            print(f"Following article link: {href}")
                            
                            # Get the article page
                            article_response = requests.get(href, headers=HEADERS)
                            if article_response.status_code == 200:
                                article_soup = BeautifulSoup(article_response.content, "html.parser")
                                
                                # Get the title
                                title_elem = article_soup.find("h1")
                                title = title_elem.text.strip() if title_elem else f"JAXA Earth Observation {downloaded_count+1}"
                                
                                # Get the description
                                desc_elem = article_soup.find("div", class_="modal__tab-description") or article_soup.find("div", class_="description")
                                desc = desc_elem.text.strip() if desc_elem else "JAXA Earth observation image."
                                
                                # Find the image - try meta og:image first
                                img_url = None
                                meta_img = article_soup.find("meta", property="og:image")
                                if meta_img and meta_img.get("content"):
                                    img_url = meta_img.get("content")
                                else:
                                    # Try to find the image in the article
                                    img = article_soup.find("img", alt=title) or article_soup.select_one("figure img") or article_soup.select_one(".earthview-image img")
                                    if img and img.get("src"):
                                        img_url = img.get("src")
                                        if not img_url.startswith("http"):
                                            img_url = source["base_url"] + ('' if img_url.startswith('/') else '/') + img_url
                                
                                if img_url:
                                    print(f"Processing JAXA image: {title}")
                                    if save_image_data("JAXA", title, img_url, desc, "jaxa_images", force_redownload):
                                        downloaded_count += 1
                                    time.sleep(1)
                        except Exception as e:
                            print(f"Error processing Earth-graphy article: {e}")
            
            # If we still haven't found any images, try a generic approach
            if downloaded_count == 0 or (source == jaxa_sources[-1] and downloaded_count < 3):
                print("Trying generic approach to find images...")
                
                # Look for any img tags that seem to be content images (not interface elements)
                content_imgs = []
                all_imgs = soup.find_all("img")
                
                for img in all_imgs:
                    src = img.get("src", "")
                    # Skip small interface images
                    if src and ("data" in src.lower() or "content" in src.lower() or "img" in src.lower()) and not ("icon" in src.lower() or "logo" in src.lower() or "button" in src.lower()):
                        img_width = img.get("width")
                        img_height = img.get("height")
                        
                        # Skip very small images
                        if img_width and img_height and int(img_width) < 100 and int(img_height) < 100:
                            continue
                            
                        content_imgs.append(img)
                
                if content_imgs:
                    print(f"Found {len(content_imgs)} potential content images")
                    
                    for img in content_imgs[:5]:
                        if downloaded_count >= max_images:
                            break
                            
                        try:
                            img_url = img.get("src")
                            if not img_url.startswith("http"):
                                img_url = source["base_url"] + ('' if img_url.startswith('/') else '/') + img_url
                            
                            title = img.get("alt") or f"JAXA Earth Observation {downloaded_count+1}"
                            desc = "JAXA satellite Earth observation image."
                            
                            print(f"Processing JAXA image: {title}")
                            if save_image_data("JAXA", title, img_url, desc, "jaxa_images", force_redownload):
                                downloaded_count += 1
                            time.sleep(1)
                        except Exception as e:
                            print(f"Error processing content image: {e}")
        
        except Exception as e:
            print(f"Error accessing {source['name']}: {e}")
    
    if downloaded_count == 0:
        print("No JAXA images found or all images already exist. All website structures may have changed.")
    else:
        print(f"JAXA scraping complete - downloaded {downloaded_count} images") 