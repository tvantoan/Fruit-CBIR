"""
Batch index the entire fruit dataset into PostgreSQL.

Usage:
    cd backend
    python scripts/index_dataset.py           # index (skip duplicates)
    python scripts/index_dataset.py --clear    # clear tables first, then index
"""
import os
import sys
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from database.db_manager import get_connection, insert_image_batch, init_db
from app.api.search_interface import extract_features

DATASET_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'Fruits_data_processed')
BATCH_COMMIT_SIZE = 500


def index_all(clear=False):
    init_db()

    conn = get_connection()
    try:
        if clear:
            print("Clearing existing data...")
            with conn.cursor() as cur:
                cur.execute("DELETE FROM features")
                cur.execute("DELETE FROM query_logs")
                cur.execute("DELETE FROM images")
            conn.commit()
            print("Tables cleared.")

        count = 0
        skipped = 0

        for category_dir in sorted(os.listdir(DATASET_PATH)):
            category_path = os.path.join(DATASET_PATH, category_dir)
            if not os.path.isdir(category_path):
                continue

            fruit_label = category_dir.replace('_processed', '')
            print(f"Indexing {fruit_label}...")

            for filename in sorted(os.listdir(category_path)):
                if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    continue

                abs_path = os.path.join(category_path, filename)
                # Store relative path: "Apples_processed/Apple_1.png"
                rel_path = f"{category_dir}/{filename}"
                file_size_kb = os.path.getsize(abs_path) / 1024

                image_id = insert_image_batch(
                    conn,
                    filename=filename,
                    filepath=rel_path,
                    fruit_label=fruit_label,
                    width=224,
                    height=224,
                    file_size_kb=round(file_size_kb, 2)
                )

                if image_id is not None:
                    extract_features(image_id, abs_path)
                    count += 1
                else:
                    skipped += 1

                if (count + skipped) % BATCH_COMMIT_SIZE == 0:
                    conn.commit()
                    print(f"  ...processed {count + skipped} images ({count} new, {skipped} skipped)")

            conn.commit()

        print(f"\nDone! Indexed {count} new images, skipped {skipped} duplicates. Total processed: {count + skipped}.")
    finally:
        conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Index fruit dataset into PostgreSQL')
    parser.add_argument('--clear', action='store_true', help='Clear all tables before indexing')
    args = parser.parse_args()
    index_all(clear=args.clear)
