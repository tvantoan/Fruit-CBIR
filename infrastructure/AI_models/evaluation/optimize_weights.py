"""
Grid search to find optimal feature weights for Fruit-CBIR.

Pre-extracts query features once (fast — skips rembg since dataset is preprocessed)
then sweeps weight combinations and reports best by Mean P@5.

Usage:
    python -m infrastructure.AI_models.evaluation.optimize_weights
"""
import json
import os
import sys
from itertools import product

import cv2
from dotenv import load_dotenv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
GROUND_TRUTH_PATH = os.path.join(os.path.dirname(__file__), 'ground_truth.json')
DATASET_ROOT = os.path.join(PROJECT_ROOT, 'static', 'Fruits_data_processed')

sys.path.insert(0, PROJECT_ROOT)
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))


def precision_at_k(results, expected_label, k=5):
    return sum(1 for r in results[:k] if r['fruit_name'] == expected_label) / k


def average_precision(results, expected_label, k=5):
    hits = 0
    s = 0.0
    for i, r in enumerate(results[:k]):
        if r['fruit_name'] == expected_label:
            hits += 1
            s += hits / (i + 1)
    return 0.0 if hits == 0 else s / hits


def main():
    from app import app
    from infrastructure.database.database import Database
    from infrastructure.repositories import FeatureRepository
    from usecases.feature_extractor import FeatureExtractor

    with app.app_context():
        Database.initialize()

        with open(GROUND_TRUTH_PATH, encoding='utf-8') as f:
            gt = json.load(f)

        fx = FeatureExtractor()
        feature_repo = FeatureRepository()

        # Pre-extract features for all 29 queries (skip rembg since already preprocessed)
        print(f"Extracting features for {len(gt['queries'])} query images...")
        query_features = []
        for q in gt['queries']:
            img_path = os.path.join(DATASET_ROOT, q['query_image'])
            img = cv2.imread(img_path)
            if img is None:
                continue
            feats = fx.execute(img)
            query_features.append((q['fruit_label'], feats))
        print(f"  Extracted {len(query_features)} feature sets.\n")

        # Define grid: weights sum to 1.0
        # Search space: each weight in [0.0, 0.1, 0.2, ..., 1.0] but we only test combos summing to 1
        steps = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        results_log = []

        combos = []
        for c in steps:
            for cm in steps:
                for t in steps:
                    for g in steps:
                        s = round(1.0 - c - cm - t - g, 2)
                        if 0.0 <= s <= 0.8 and abs(c + cm + t + g + s - 1.0) < 0.01:
                            combos.append((c, cm, t, g, s))

        print(f"Searching {len(combos)} weight combinations...\n")

        best_p5 = -1.0
        best_weights = None
        best_map = -1.0

        for i, (c, cm, t, g, s) in enumerate(combos):
            weights = {
                'color': c, 'color_moments': cm,
                'texture': t, 'glcm': g, 'shape': s,
            }
            p5_list = []
            ap_list = []
            for label, feats in query_features:
                results = feature_repo.search_similar(feats, weights)
                p5_list.append(precision_at_k(results, label))
                ap_list.append(average_precision(results, label))
            mean_p5 = sum(p5_list) / len(p5_list)
            mean_ap = sum(ap_list) / len(ap_list)
            results_log.append((mean_p5, mean_ap, weights))

            if mean_p5 > best_p5 or (mean_p5 == best_p5 and mean_ap > best_map):
                best_p5 = mean_p5
                best_map = mean_ap
                best_weights = weights
                print(f"  [{i+1}/{len(combos)}] NEW BEST P@5={mean_p5:.4f} mAP={mean_ap:.4f}  "
                      f"(c={c}, cm={cm}, t={t}, g={g}, s={s})")
            elif (i + 1) % 50 == 0:
                print(f"  [{i+1}/{len(combos)}] current P@5={mean_p5:.4f}")

        print(f"\n{'='*70}")
        print(f"  BEST WEIGHTS:  P@5 = {best_p5:.4f}, mAP = {best_map:.4f}")
        print(f"    color         = {best_weights['color']}")
        print(f"    color_moments = {best_weights['color_moments']}")
        print(f"    texture       = {best_weights['texture']}")
        print(f"    glcm          = {best_weights['glcm']}")
        print(f"    shape         = {best_weights['shape']}")
        print(f"{'='*70}\n")

        # Show top 10 for context
        results_log.sort(key=lambda x: (x[0], x[1]), reverse=True)
        print("Top 10 weight combinations:")
        print(f"  {'P@5':<7s} {'mAP':<7s} | color  cm     t      glcm   shape")
        print(f"  {'-'*7} {'-'*7} | {'-'*40}")
        for p5, mp, w in results_log[:10]:
            print(f"  {p5:.4f}  {mp:.4f}  | {w['color']:.2f}   {w['color_moments']:.2f}   "
                  f"{w['texture']:.2f}   {w['glcm']:.2f}   {w['shape']:.2f}")


if __name__ == '__main__':
    main()
