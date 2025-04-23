import argparse
from utils import setup_csv
from esa_scraper import scrape_esa_images
from nasa_scraper import scrape_nasa_images
from jaxa_scraper import scrape_jaxa_images
from apod_scraper import scrape_apod_images

def parse_args():
    parser = argparse.ArgumentParser(description="Download images from space agencies")
    parser.add_argument("--force", "-f", action="store_true", help="Force redownload of images even if they already exist")
    parser.add_argument("--apod-days", "-a", type=int, default=7, help="Number of days to download from NASA APOD (default: 7)")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    force_redownload = args.force
    apod_days = args.apod_days
    
    if force_redownload:
        print("WARNING: Force redownload mode enabled. All images will be re-downloaded.")
        
    setup_csv()
    scrape_esa_images(force_redownload)
    scrape_nasa_images(force_redownload)
    scrape_jaxa_images(force_redownload)
    scrape_apod_images(apod_days, force_redownload) 