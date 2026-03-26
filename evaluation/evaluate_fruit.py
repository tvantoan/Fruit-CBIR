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

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROUND_TRUTH_PATH = os.path.join(PROJECT_ROOT, 'evaluation', 'ground_truth.json')
API_BASE = 'http://localhost:5001/api'

# Setup backend imports for direct mode
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'backend'))
from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, 'backend', '.env'))


def load_ground_truth():
    with open(GROUND_TRUTH_PATH, encoding='utf-8') as f:
        return json.load(f)


def find_image_id(filename, fruit_label):
    """Lookup image_id in DB by filename + label."""
    from database.db_manager import find_image_by_filename
    return find_image_by_filename(os.path.basename(filename), fruit_label)


def search_direct(image_id, top_k=5):
    """Call search_similar directly (no HTTP)."""
    from app.api.search_interface import search_similar
    start = time.time()
    results = search_similar(image_id, top_k=top_k)
    elapsed_ms = round((time.time() - start) * 1000, 2)
    return results, elapsed_ms


def search_api(image_id, top_k=5):
    """Call Flask API endpoint."""
    import requests
    resp = requests.get(f"{API_BASE}/search", params={"image_id": image_id})
    resp.raise_for_status()
    data = resp.json()
    return data['results'], data['query_time_ms']


def precision_at_k(results, expected_label, k=5):
    """P@k: fraction of top-k results with matching fruit_label."""
    relevant = sum(1 for r in results[:k] if r['fruit_label'] == expected_label)
    return relevant / k


def average_precision(results, expected_label, k=5):
    """AP@k for a single query."""
    hits = 0
    sum_precision = 0.0
    for i, r in enumerate(results[:k]):
        if r['fruit_label'] == expected_label:
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
