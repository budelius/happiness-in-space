import argparse
from utils import setup_csv, regenerate_all_overlays
from esa_scraper import scrape_esa_images
from nasa_scraper import scrape_nasa_images
from jaxa_scraper import scrape_jaxa_images
from apod_scraper import scrape_apod_images
from cnsa_scraper import scrape_cnsa_images

def parse_args():
    parser = argparse.ArgumentParser(description="Download images from space agencies")
    parser.add_argument("--force", "-f", action="store_true", help="Force redownload of images even if they already exist")
    parser.add_argument("--apod-days", "-a", type=int, default=7, help="Number of days to download from NASA APOD (default: 7)")
    parser.add_argument("--recreate-overlays", "-r", action="store_true", help="Only recreate overlay images using existing originals")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    force_download = args.force
    apod_days = args.apod_days
    recreate_overlays = args.recreate_overlays
    
    if force_download and recreate_overlays:
        print("WARNING: --force and --recreate-overlays are mutually exclusive. Using --recreate-overlays only.")
        force_download = False
    
    if force_download:
        print("WARNING: Force download mode enabled. All images will be downloaded again.")
    
    if recreate_overlays:
        print("Recreate overlays mode enabled. Will regenerate all overlay images.")
        # Regenerate overlays for all image directories
        regenerate_all_overlays("esa_images")
        regenerate_all_overlays("nasa_images")
        regenerate_all_overlays("jaxa_images")
        regenerate_all_overlays("apod_images")
        regenerate_all_overlays("cnsa_images")
    else:
        # Normal operation - download images
        setup_csv()
        scrape_esa_images(force_download, recreate_overlays)
        scrape_nasa_images(force_download, recreate_overlays)
        scrape_jaxa_images(force_download, recreate_overlays)
        scrape_apod_images(apod_days, force_download, recreate_overlays)
        scrape_cnsa_images(force_download, recreate_overlays)