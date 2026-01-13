import requests
import zipfile
import io
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATA_URL = "https://files.grouplens.org/datasets/movielens/ml-100k.zip"
TARGET_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

def download_and_extract():
    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR)
        
    logger.info(f"Downloading dataset from {DATA_URL}...")
    try:
        r = requests.get(DATA_URL)
        r.raise_for_status()
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(TARGET_DIR)
        logger.info(f"Dataset extracted to {TARGET_DIR}")
        
        # Verify extraction
        extracted_path = os.path.join(TARGET_DIR, 'ml-100k', 'u.data')
        if os.path.exists(extracted_path):
            logger.info("Verification successful: u.data found.")
        else:
            logger.error("Verification failed: u.data not found.")
            
    except Exception as e:
        logger.error(f"Failed to download/extract data: {e}")

if __name__ == "__main__":
    download_and_extract()
