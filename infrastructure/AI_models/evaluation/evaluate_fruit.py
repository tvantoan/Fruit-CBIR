"""
Fruit CBIR Evaluation Script.

Measures Precision@5 and Mean Average Precision (mAP) using ground_truth.json.

Usage:
    cd Fruit-CBIR
    python evaluation/evaluate_fruit.py                    # direct mode (default)
    python evaluation/evaluate_fruit.py --mode api         # via Flask API
    python evaluation/evaluate_fruit.py --top-k 10         # top-10 instead of top-5
"""
import json
import os
import sys
import time
import argparse

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
GROUND_TRUTH_PATH = os.path.join(os.path.dirname(__file__), 'ground_truth.json')
API_BASE = 'http://localhost:5001/api'

# Setup imports for direct mode
sys.path.insert(0, PROJECT_ROOT)
from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))


def load_ground_truth():
    with open(GROUND_TRUTH_PATH, encoding='utf-8') as f:
        return json.load(f)


def find_image_id(filename, fruit_label):
    """Lookup image_id in DB by filename + label."""
    from infrastructure.repositories import ImageRepository

    repo = ImageRepository()
    # Note: This method may not exist in current ImageRepository interface
    # You might need to add a find_by_filename method
    return repo.get_by_id(1)  # Placeholder - needs actual implementation


def search_direct(image_id, top_k=5):
    """Execute search use case directly (no HTTP)."""
    from infrastructure.repositories import ImageRepository, FeatureRepository, FruitRepository
    from usecases.feature_extractor import FeatureExtractor
    from usecases.remove_background import BackgroundRemover
    from usecases.search_images import SearchImagesUseCase

    # Get image path from DB first
    image_repo = ImageRepository()
    image = image_repo.get_by_id(image_id)
    if not image:
        raise ValueError(f"Image {image_id} not found")

    feature_repo = FeatureRepository()
    fruit_repo = FruitRepository()
    use_case = SearchImagesUseCase(
        image_repo=image_repo,
        feature_repo=feature_repo,
        feature_extractor=FeatureExtractor(),
        fruit_repo=fruit_repo,
        background_remover=BackgroundRemover()
    )

    # Construct full image path
    dataset_root = os.path.join(os.path.dirname(__file__), '..', '..', 'static', 'Fruits_data_processed')
    image_path = os.path.join(dataset_root, image.filepath)

    start = time.time()
    entities = use_case.execute(image_path=image_path, top_k=top_k)
    elapsed_ms = round((time.time() - start) * 1000, 2)

    # Convert SearchResult objects to dicts
    return [{attr: getattr(result, attr) for attr in ['image_id', 'filename', 'filepath', 'fruit_id', 'similarity', 'distance']} for result in entities], elapsed_ms


def search_api(image_id, top_k=5):
    """Call Flask API endpoint."""
    import requests
    resp = requests.get(f"{API_BASE}/search", params={"image_id": image_id, "top_k": top_k})
    resp.raise_for_status()
    data = resp.json()
    return data['results'], data['query_time_ms']


def precision_at_k(results, expected_label, k=5):
    """P@k: fraction of top-k results with matching fruit_label (using filename-based label)."""
    relevant = sum(1 for r in results[:k] if r['fruit_label'] == expected_label)
    return relevant / k


def average_precision(results, expected_label, k=5):
    """AP@k for a single query (using filename-based label)."""
    hits = 0
    sum_precision = 0.0
    for i, r in enumerate(results[:k]):
        # Extract fruit label from filename (format: "fruit_name_xxx.jpg")
        result_label = os.path.basename(r.get('filepath', '')).split('_')[0]
        if result_label == expected_label:
            hits += 1
            sum_precision += hits / (i + 1)
    if hits == 0:
        return 0.0
    return sum_precision / hits


def run_evaluation(mode='direct', top_k=5):
    gt = load_ground_truth()
    search_fn = search_direct if mode == 'direct' else search_api

    results_table = []
    category_scores = {}

    print(f"\n{'='*70}")
    print(f"  Fruit CBIR Evaluation  |  mode={mode}  |  top_k={top_k}")
    print(f"  Ground truth: {gt['total_queries']} queries")
    print(f"{'='*70}\n")

    for query in gt['queries']:
        image_id = find_image_id(query['query_image'], query['fruit_label'])
        if image_id is None:
            print(f"  SKIP: {query['query_image']} not found in DB")
            continue

        search_results, query_ms = search_fn(image_id, top_k)

        p_k = precision_at_k(search_results, query['fruit_label'], top_k)
        ap = average_precision(search_results, query['fruit_label'], top_k)

        results_table.append({
            'query': query['query_image'],
            'label': query['fruit_label'],
            'p_at_k': p_k,
            'ap': ap,
            'time_ms': query_ms,
        })

        cat = query['fruit_label']
        category_scores.setdefault(cat, []).append(p_k)

    # Print per-query results
    print(f"  {'Query':<42s} | {'Label':<14s} | P@{top_k:<2d} | AP    | Time")
    print(f"  {'-'*42}-+-{'-'*14}-+------+-------+-------")
    for r in results_table:
        print(f"  {r['query']:<42s} | {r['label']:<14s} | {r['p_at_k']:.2f} | {r['ap']:.3f} | {r['time_ms']:.1f}ms")

    # Per-category summary
    print(f"\n  {'Category':<14s} | Mean P@{top_k} | Queries")
    print(f"  {'-'*14}-+-{'-'*9}-+--------")
    for cat in sorted(category_scores.keys()):
        scores = category_scores[cat]
        mean_p = sum(scores) / len(scores)
        print(f"  {cat:<14s} | {mean_p:.4f}   | {len(scores)}")

    # Overall metrics
    all_pk = [r['p_at_k'] for r in results_table]
    all_ap = [r['ap'] for r in results_table]
    all_time = [r['time_ms'] for r in results_table]

    if all_pk:
        print(f"\n{'='*70}")
        print(f"  OVERALL:")
        print(f"    Mean P@{top_k}:     {sum(all_pk)/len(all_pk):.4f}")
        print(f"    mAP:           {sum(all_ap)/len(all_ap):.4f}")
        print(f"    Avg query time: {sum(all_time)/len(all_time):.1f} ms")
        print(f"    Total queries:  {len(all_pk)}")
        print(f"{'='*70}\n")
    else:
        print("\n  No queries evaluated. Is the dataset indexed?\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Evaluate Fruit CBIR system')
    parser.add_argument('--mode', choices=['direct', 'api'], default='direct',
                        help='direct = import search_similar; api = call Flask endpoint')
    parser.add_argument('--top-k', type=int, default=5, help='Number of results to evaluate')
    args = parser.parse_args()
    run_evaluation(mode=args.mode, top_k=args.top_k)
