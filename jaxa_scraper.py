from utils import save_image_data, HEADERS
import time
import requests
from bs4 import BeautifulSoup
import re

def scrape_jaxa_images(force_redownload=False, recreate_overlays=False):
    if recreate_overlays:
        print("JAXA: Recreate overlays mode - skipping image scraping")
        return
        
    print("Scraping JAXA Digital Archives...")
    
    # Use JAXA Digital Archives as the source
    jaxa_archive_url = "https://jda.jaxa.jp/?lang=e"
    downloaded_count = 0
    max_images = 20  # Set a limit on total images to download
    
    try:
        # Access the main page
        response = requests.get(jaxa_archive_url, headers=HEADERS)
        if response.status_code != 200:
            print(f"Failed to access JAXA Digital Archives: {response.status_code}")
            return
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Look for category links - these might lead to image galleries
        categories = []
        
        # Try to find the category containers
        category_divs = soup.select('.category') or soup.select('[class*="category"]') or soup.select('.CATEGORY')
        
        if category_divs:
            for div in category_divs:
                link = div.find('a')
                if link and link.get('href'):
                    href = link.get('href')
                    # Make sure we have an absolute URL
                    if not href.startswith('http'):
                        # Check if it's a root-relative URL or page-relative URL
                        if href.startswith('/'):
                            href = "https://jda.jaxa.jp" + href
                        else:
                            href = "https://jda.jaxa.jp/" + href
                    categories.append(href)
        
        # If no categories found, try looking for cards or image containers
        if not categories:
            # Try to find featured images or PICK UP section
            pickup_links = soup.select('.pickup a') or soup.select('[class*="pick"] a') or soup.select('#PICK_UP a')
            if pickup_links:
                for link in pickup_links:
                    href = link.get('href')
                    if href:
                        # Make sure we have an absolute URL
                        if not href.startswith('http'):
                            if href.startswith('/'):
                                href = "https://jda.jaxa.jp" + href
                            else:
                                href = "https://jda.jaxa.jp/" + href
                        categories.append(href)
        
        # If still no categories, check for any image links
        if not categories:
            image_links = []
            all_links = soup.find_all('a')
            for link in all_links:
                href = link.get('href', '')
                # Look for links that likely lead to images
                if href and ('detail' in href.lower() or 'photo' in href.lower() or 'image' in href.lower()):
                    # Make sure we have an absolute URL
                    if not href.startswith('http'):
                        if href.startswith('/'):
                            href = "https://jda.jaxa.jp" + href
                        else:
                            href = "https://jda.jaxa.jp/" + href
                    
                    image_links.append(href)
                    
            categories = image_links
        
        # Look for images directly on the main page
        main_page_images = []
        img_tags = soup.find_all('img')
        for img in img_tags:
            src = img.get('src', '')
            # Skip logos, icons, buttons
            if src and not ('logo' in src.lower() or 'icon' in src.lower() or 'button' in src.lower()):
                # Check if it's a content image (larger than icons)
                width = img.get('width', '')
                height = img.get('height', '')
                if (not width or int(width) > 150) and (not height or int(height) > 150):
                    if not src.startswith('http'):
                        if src.startswith('/'):
                            src = "https://jda.jaxa.jp" + src
                        else:
                            src = "https://jda.jaxa.jp/" + src
                    
                    # Get caption/title from alt or parent elements
                    title = img.get('alt', '') or (img.parent.get_text().strip() if img.parent else '')
                    if not title:
                        # Check if there's a nearby caption
                        caption = img.find_next('figcaption') or img.find_next('div', class_='caption')
                        if caption:
                            title = caption.get_text().strip()
                    
                    if not title:
                        title = f"JAXA Archive Image {len(main_page_images) + 1}"
                    
                    main_page_images.append({
                        'url': src,
                        'title': title,
                        'desc': "JAXA satellite or space mission image."
                    })
        
        # Process direct images from main page first
        for img_data in main_page_images:
            if downloaded_count >= max_images:
                break
                
            try:
                print(f"Processing JAXA image: {img_data['title']}")
                if save_image_data("JAXA", img_data['title'], img_data['url'], img_data['desc'], "jaxa_images", force_redownload, recreate_overlays):
                    downloaded_count += 1
                time.sleep(1)
            except Exception as e:
                print(f"Error processing main page image: {e}")
        
        # Now go through category/gallery pages
        for idx, category_url in enumerate(categories):
            if downloaded_count >= max_images:
                break
                
            try:
                print(f"Accessing category/gallery page: {category_url}")
                category_response = requests.get(category_url, headers=HEADERS)
                if category_response.status_code != 200:
                    print(f"Failed to access category page: {category_response.status_code}")
                    continue
                
                category_soup = BeautifulSoup(category_response.content, "html.parser")
                
                # Look for content images in the category page
                img_containers = category_soup.select('.img-container') or category_soup.select('.photo') or category_soup.select('.image') or category_soup.select('figure')
                
                if not img_containers:
                    # If no containers found, look for img tags directly
                    img_containers = category_soup.find_all('img')
                    
                print(f"Found {len(img_containers)} potential image containers")
                
                for container in img_containers:
                    if downloaded_count >= max_images:
                        break
                        
                    try:
                        # If the container itself is an img tag
                        if container.name == 'img':
                            img = container
                        else:
                            img = container.find('img')
                            
                        if not img or not img.get('src'):
                            continue
                            
                        img_url = img.get('src')
                        # Make absolute URL if needed
                        if not img_url.startswith('http'):
                            if img_url.startswith('/'):
                                img_url = "https://jda.jaxa.jp" + img_url
                            else:
                                img_url = "https://jda.jaxa.jp/" + img_url
                        
                        # Check if this is a thumbnail and there's a link to a larger image
                        parent_link = img.find_parent('a')
                        if parent_link and parent_link.get('href'):
                            href = parent_link.get('href')
                            # Check if link points to a full-size image
                            if href.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                                if not href.startswith('http'):
                                    if href.startswith('/'):
                                        href = "https://jda.jaxa.jp" + href
                                    else:
                                        href = "https://jda.jaxa.jp/" + href
                                img_url = href
                            # Or if it's a link to a detail page
                            elif 'detail' in href.lower() or 'photo' in href.lower():
                                try:
                                    if not href.startswith('http'):
                                        if href.startswith('/'):
                                            href = "https://jda.jaxa.jp" + href
                                        else:
                                            href = "https://jda.jaxa.jp/" + href
                                            
                                    # Follow link to detail page
                                    detail_response = requests.get(href, headers=HEADERS)
                                    if detail_response.status_code == 200:
                                        detail_soup = BeautifulSoup(detail_response.content, "html.parser")
                                        
                                        # Look for the full-size image
                                        detail_img = detail_soup.select_one('.full-image img') or detail_soup.select_one('.detail-image img') or detail_soup.select_one('figure img')
                                        
                                        if detail_img and detail_img.get('src'):
                                            full_img_url = detail_img.get('src')
                                            if not full_img_url.startswith('http'):
                                                if full_img_url.startswith('/'):
                                                    full_img_url = "https://jda.jaxa.jp" + full_img_url
                                                else:
                                                    full_img_url = "https://jda.jaxa.jp/" + full_img_url
                                            img_url = full_img_url
                                except Exception as e:
                                    print(f"Error following detail link: {e}")
                        
                        # Get title from alt text, figcaption, or parent text
                        title = img.get('alt', '')
                        if not title:
                            # Check for caption
                            figcaption = container.find('figcaption') if container.name != 'img' else None
                            if figcaption:
                                title = figcaption.get_text().strip()
                            else:
                                title_tag = container.find('h2') or container.find('h3') or container.find('div', class_='title')
                                if title_tag:
                                    title = title_tag.get_text().strip()
                        
                        if not title:
                            title = f"JAXA Space Image {downloaded_count + 1}"
                            
                        # Get description
                        desc = ""
                        desc_elem = container.find('p', class_='description') or container.find('div', class_='description')
                        if desc_elem:
                            desc = desc_elem.get_text().strip()
                        else:
                            # Use default description
                            desc = "JAXA satellite or space mission image from JAXA Digital Archives."
                        
                        print(f"Processing JAXA image: {title}")
                        if save_image_data("JAXA", title, img_url, desc, "jaxa_images", force_redownload, recreate_overlays):
                            downloaded_count += 1
                        time.sleep(1)
                    except Exception as e:
                        print(f"Error processing image container: {e}")
            except Exception as e:
                print(f"Error accessing category {idx+1}: {e}")
                
        # If we still don't have enough images, try a generic approach
        if downloaded_count < 5:
            print("Trying additional image search across the site...")
            
            # Search for other images that might be higher quality
            search_url = "https://jda.jaxa.jp/search.php?lang=e"
            try:
                search_response = requests.get(search_url, headers=HEADERS)
                if search_response.status_code == 200:
                    search_soup = BeautifulSoup(search_response.content, "html.parser")
                    
                    # Look for search results or featured content
                    search_results = search_soup.select('.search-result') or search_soup.select('.result-item') or search_soup.select('.gallery-item')
                    
                    if search_results:
                        print(f"Found {len(search_results)} search results")
                        
                        for result in search_results:
                            if downloaded_count >= max_images:
                                break
                                
                            try:
                                # Find the image
                                img = result.find('img')
                                if not img or not img.get('src'):
                                    continue
                                    
                                img_url = img.get('src')
                                if not img_url.startswith('http'):
                                    if img_url.startswith('/'):
                                        img_url = "https://jda.jaxa.jp" + img_url
                                    else:
                                        img_url = "https://jda.jaxa.jp/" + img_url
                                
                                # Check for title
                                title_elem = result.find('h3') or result.find('h4') or result.find('div', class_='title')
                                title = title_elem.get_text().strip() if title_elem else img.get('alt', '')
                                
                                if not title:
                                    title = f"JAXA Space Image {downloaded_count + 1}"
                                
                                # Description
                                desc_elem = result.find('p', class_='description') or result.find('div', class_='description')
                                desc = desc_elem.get_text().strip() if desc_elem else "JAXA satellite or space mission image from JAXA Digital Archives."
                                
                                print(f"Processing JAXA image: {title}")
                                if save_image_data("JAXA", title, img_url, desc, "jaxa_images", force_redownload, recreate_overlays):
                                    downloaded_count += 1
                                time.sleep(1)
                            except Exception as e:
                                print(f"Error processing search result: {e}")
            except Exception as e:
                print(f"Error with search approach: {e}")
    
    except Exception as e:
        print(f"Error accessing JAXA Digital Archives: {e}")
    
    if downloaded_count == 0:
        print("No JAXA images found or all images already exist. Website structure may have changed.")
    else:
        print(f"JAXA scraping complete - downloaded {downloaded_count} images") 