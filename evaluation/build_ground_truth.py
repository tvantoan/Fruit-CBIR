"""
Build ground truth evaluation set for Fruit-CBIR.

Deterministically selects 3-4 query images per category and assigns
5 expected similar images (same category) for each query.

Usage:
    python evaluation/build_ground_truth.py
"""
import json
import os

DATASET_PATH = os.path.join(os.path.dirname(__file__), '..', 'Fruits_data_processed')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), 'ground_truth.json')

# Small categories (<=310 images) get 3 queries, large ones get 4
SMALL_THRESHOLD = 500


def get_evenly_spaced(items, n):
    """Pick n items at evenly spaced indices from a sorted list."""
    if n >= len(items):
        return items[:n]
    step = len(items) / (n + 1)
    return [items[int(step * (i + 1))] for i in range(n)]


def build_ground_truth():
    queries = []

    for category_dir in sorted(os.listdir(DATASET_PATH)):
        category_path = os.path.join(DATASET_PATH, category_dir)
        if not os.path.isdir(category_path):
            continue

        fruit_label = category_dir.replace('_processed', '')
        files = sorted([
            f for f in os.listdir(category_path)
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        ])

        if len(files) < 10:
            print(f"  Skipping {fruit_label}: only {len(files)} images")
            continue

        # Decide how many queries for this category
        n_queries = 3 if len(files) <= SMALL_THRESHOLD else 4
        query_files = get_evenly_spaced(files, n_queries)

        for query_file in query_files:
            # Pick 5 expected results from the same category (excluding the query itself)
            remaining = [f for f in files if f != query_file]
            expected = get_evenly_spaced(remaining, 5)

            queries.append({
                'query_image': f"{category_dir}/{query_file}",
                'fruit_label': fruit_label,
                'expected_top5': [f"{category_dir}/{f}" for f in expected],
            })

    ground_truth = {
        'version': '1.0',
        'description': 'Ground truth for Fruit-CBIR evaluation. Correct = same fruit category.',
        'evaluation_metric': 'category_match',
        'total_queries': len(queries),
        'queries': queries,
    }

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(ground_truth, f, indent=2, ensure_ascii=False)

    print(f"Ground truth generated: {len(queries)} queries")
    for q in queries:
        print(f"  {q['fruit_label']:15s} -> {os.path.basename(q['query_image'])}")
    print(f"\nSaved to: {OUTPUT_PATH}")


if __name__ == '__main__':
    build_ground_truth()
