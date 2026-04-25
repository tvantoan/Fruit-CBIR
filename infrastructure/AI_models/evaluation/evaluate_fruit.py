"""
Fruit CBIR Evaluation Script (Clean Architecture).

Measures Precision@5 and Mean Average Precision (mAP) using ground_truth.json.

Usage:
    cd Fruit-CBIR
    python -m infrastructure.AI_models.evaluation.evaluate_fruit                    # direct mode
    python -m infrastructure.AI_models.evaluation.evaluate_fruit --mode api         # via Flask API
    python -m infrastructure.AI_models.evaluation.evaluate_fruit --top-k 10
    python -m infrastructure.AI_models.evaluation.evaluate_fruit --weights 0.7,0.2,0.1
"""
import argparse
import json
import os
import sys
import time

import cv2
from dotenv import load_dotenv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
GROUND_TRUTH_PATH = os.path.join(os.path.dirname(__file__), 'ground_truth.json')
DATASET_ROOT = os.path.join(PROJECT_ROOT, 'static', 'Fruits_data_processed')
API_BASE = 'http://localhost:5001/api'

sys.path.insert(0, PROJECT_ROOT)
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))


def load_ground_truth():
    with open(GROUND_TRUTH_PATH, encoding='utf-8') as f:
        return json.load(f)


def search_direct(image_path, weights, app_context):
    """Run search use case directly (no HTTP). Requires Flask app context for SQLAlchemy."""
    from infrastructure.repositories import ImageRepository, FeatureRepository, FruitRepository
    from usecases.feature_extractor import FeatureExtractor
    from usecases.remove_background import BackgroundRemover
    from usecases.search_images import SearchImagesUseCase

    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Cannot read image: {image_path}")

    use_case = SearchImagesUseCase(
        image_repo=ImageRepository(),
        feature_repo=FeatureRepository(),
        feature_extractor=FeatureExtractor(),
        fruit_repo=FruitRepository(),
        background_remover=BackgroundRemover(),
    )

    start = time.time()
    results = use_case.execute(image_data=image, weights=weights)
    elapsed_ms = round((time.time() - start) * 1000, 2)
    return results, elapsed_ms


def search_api(image_path, weights, top_k):
    """Call Flask API endpoint POST /api/search with multipart upload."""
    import requests

    with open(image_path, 'rb') as f:
        files = {'image': (os.path.basename(image_path), f, 'image/png')}
        data = {
            'top_k': top_k,
            'weight_color': weights['color'],
            'weight_texture': weights['texture'],
            'weight_shape': weights['shape'],
        }
        resp = requests.post(f"{API_BASE}/search", files=files, data=data)
    resp.raise_for_status()
    payload = resp.json()
    results = payload['results']
    elapsed_ms = payload.get('query_stats', {}).get('query_time_ms', 0)
    return results, elapsed_ms


def precision_at_k(results, expected_label, k=5):
    """P@k: fraction of top-k results with matching fruit_name."""
    relevant = sum(1 for r in results[:k] if _get_label(r) == expected_label)
    return relevant / k


def average_precision(results, expected_label, k=5):
    """AP@k for a single query."""
    hits = 0
    sum_precision = 0.0
    for i, r in enumerate(results[:k]):
        if _get_label(r) == expected_label:
            hits += 1
            sum_precision += hits / (i + 1)
    if hits == 0:
        return 0.0
    return sum_precision / hits


def _get_label(result):
    """Extract fruit name from result (handles both dict and dataclass)."""
    if hasattr(result, 'fruit_name'):
        return result.fruit_name
    return result.get('fruit_name', '')


def run_evaluation(mode='direct', top_k=5, weights=None):
    if weights is None:
        weights = {'color': 0.7, 'texture': 0.2, 'shape': 0.1}

    gt = load_ground_truth()
    results_table = []
    category_scores = {}

    print(f"\n{'='*70}")
    print(f"  Fruit CBIR Evaluation  |  mode={mode}  |  top_k={top_k}")
    print(f"  Weights: color={weights['color']}, texture={weights['texture']}, shape={weights['shape']}")
    print(f"  Ground truth: {gt['total_queries']} queries")
    print(f"{'='*70}\n")

    app_ctx = None
    if mode == 'direct':
        from app import app
        from infrastructure.database.database import Database
        app_ctx = app.app_context()
        app_ctx.push()
        Database.initialize()

    try:
        for query in gt['queries']:
            image_path = os.path.join(DATASET_ROOT, query['query_image'])
            if not os.path.exists(image_path):
                print(f"  SKIP: {query['query_image']} file not found")
                continue

            try:
                if mode == 'direct':
                    search_results, query_ms = search_direct(image_path, weights, app_ctx)
                else:
                    search_results, query_ms = search_api(image_path, weights, top_k)
            except Exception as e:
                print(f"  ERROR: {query['query_image']}: {e}")
                continue

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
    finally:
        if app_ctx is not None:
            app_ctx.pop()

    print(f"  {'Query':<42s} | {'Label':<14s} | P@{top_k:<2d} | AP    | Time")
    print(f"  {'-'*42}-+-{'-'*14}-+------+-------+-------")
    for r in results_table:
        print(f"  {r['query']:<42s} | {r['label']:<14s} | {r['p_at_k']:.2f} | {r['ap']:.3f} | {r['time_ms']:.1f}ms")

    print(f"\n  {'Category':<14s} | Mean P@{top_k} | Queries")
    print(f"  {'-'*14}-+-{'-'*9}-+--------")
    for cat in sorted(category_scores.keys()):
        scores = category_scores[cat]
        mean_p = sum(scores) / len(scores)
        print(f"  {cat:<14s} | {mean_p:.4f}   | {len(scores)}")

    all_pk = [r['p_at_k'] for r in results_table]
    all_ap = [r['ap'] for r in results_table]
    all_time = [r['time_ms'] for r in results_table]

    if all_pk:
        print(f"\n{'='*70}")
        print(f"  OVERALL:")
        print(f"    Mean P@{top_k}:      {sum(all_pk)/len(all_pk):.4f}")
        print(f"    mAP:           {sum(all_ap)/len(all_ap):.4f}")
        print(f"    Avg query time: {sum(all_time)/len(all_time):.1f} ms")
        print(f"    Total queries:  {len(all_pk)}")
        print(f"{'='*70}\n")
    else:
        print("\n  No queries evaluated. Is the dataset seeded?\n")


def parse_weights(s):
    parts = [float(x) for x in s.split(',')]
    if len(parts) != 5:
        raise argparse.ArgumentTypeError(
            "Weights must be 5 comma-separated floats: color,color_moments,texture,glcm,shape"
        )
    return {
        'color': parts[0],
        'color_moments': parts[1],
        'texture': parts[2],
        'glcm': parts[3],
        'shape': parts[4],
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Evaluate Fruit CBIR system')
    parser.add_argument('--mode', choices=['direct', 'api'], default='direct')
    parser.add_argument('--top-k', type=int, default=5)
    parser.add_argument('--weights', type=parse_weights, default=None,
                        help='Format: color,color_moments,texture,glcm,shape (e.g. 0.4,0.2,0.15,0.15,0.1)')
    args = parser.parse_args()
    run_evaluation(mode=args.mode, top_k=args.top_k, weights=args.weights)
