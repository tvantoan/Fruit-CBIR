"""
Batch index the entire fruit dataset into PostgreSQL.

Usage:
    cd backend
    python scripts/index_dataset.py

Requires: Docker PostgreSQL running, Member B's extract_features implemented (optional).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from database.db_manager import insert_image, get_connection
from app.api.search_interface import extract_features

DATASET_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'Fruits_data_processed')


def index_all():
    count = 0
    for category_dir in sorted(os.listdir(DATASET_PATH)):
        category_path = os.path.join(DATASET_PATH, category_dir)
        if not os.path.isdir(category_path):
            continue

        fruit_label = category_dir.replace('_processed', '')
        print(f"Indexing {fruit_label}...")

        for filename in sorted(os.listdir(category_path)):
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue

            filepath = os.path.join(category_path, filename)
            file_size_kb = os.path.getsize(filepath) / 1024

            image_id = insert_image(
                filename=filename,
                filepath=filepath,
                fruit_label=fruit_label,
                width=224,
                height=224,
                file_size_kb=round(file_size_kb, 2)
            )

            # Member B: once extract_features is implemented, this will
            # automatically extract and store feature vectors
            extract_features(image_id, filepath)

            count += 1
            if count % 500 == 0:
                print(f"  ...indexed {count} images")

    print(f"Done! Indexed {count} images total.")


if __name__ == '__main__':
    index_all()
