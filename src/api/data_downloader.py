import os
import requests
import zipfile
import shutil
import logging

logger = logging.getLogger(__name__)

def download_movielens_data():
    """Download MovieLens small dataset if not present"""
    DATA_DIR = os.getenv("DATA_DIR", "data/raw")
    os.makedirs(DATA_DIR, exist_ok=True)

    # Check if data already exists
    if os.path.exists(os.path.join(DATA_DIR, "ratings.csv")):
        logger.info("✅ Data files already exist, skipping download")
        return True

    logger.info("📥 Downloading MovieLens data...")

    # MovieLens small dataset (10MB)
    url = "http://files.grouplens.org/datasets/movielens/ml-latest-small.zip"
    zip_path = os.path.join(DATA_DIR, "ml-latest-small.zip")

    try:
        # Download with timeout
        logger.info("Fetching from: %s", url)
        response = requests.get(url, timeout=120)
        response.raise_for_status()

        with open(zip_path, 'wb') as f:
            f.write(response.content)

        logger.info("📦 Extracting archive...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(DATA_DIR)

        # Move files to correct location
        extracted_dir = os.path.join(DATA_DIR, "ml-latest-small")
        for file in ['ratings.csv', 'movies.csv', 'tags.csv']:
            src = os.path.join(extracted_dir, file)
            dst = os.path.join(DATA_DIR, file)
            if os.path.exists(src):
                shutil.move(src, dst)
                logger.info("✅ Moved %s", file)

        # Cleanup
        os.remove(zip_path)
        shutil.rmtree(extracted_dir, ignore_errors=True)

        logger.info("✅ MovieLens data downloaded successfully!")
        return True
    except Exception as e:
        logger.error("❌ Failed to download data: %s", str(e))
        return False
