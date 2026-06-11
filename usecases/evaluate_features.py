import os
import random
import cv2
import numpy as np
import logging
from typing import Dict, List, Any

from domain.constants import FEATURE_KEYS
from infrastructure.helper import cosine_distance, normalize_weights

logger = logging.getLogger(__name__)


class EvaluateFeaturesUseCase:
    def __init__(self, feature_extractor, dataset_root: str):
        self.feature_extractor = feature_extractor
        self.dataset_root = dataset_root

    def execute(self, subset_size: int = 100) -> Dict[str, float]:
        """
        Tính mAP cho từng feature riêng lẻ trên một subset của dataset.
        Trả về dict với key là tên feature, value là mAP.
        """
        logger.info(f"Starting feature evaluation on subset of {subset_size} images")

        queries = self._prepare_queries(subset_size)

        if not queries:
            error_msg = "No valid queries found"
            logger.error(error_msg)
            return {"error": error_msg}

        logger.info(f"Prepared {len(queries)} queries for evaluation")

        results = {}

        for feature in FEATURE_KEYS:
            logger.info(f"Evaluating feature: {feature}")
            weights = normalize_weights(
                {f: 1.0 if f == feature else 0.0 for f in FEATURE_KEYS}
            )
            mAP = self._evaluate_single_feature(queries, weights, top_k=5)
            results[feature] = mAP
            logger.info(f"Feature {feature}: mAP = {mAP}")

        return results

    def _prepare_queries(self, subset_size: int) -> List[Dict]:
        """Chuẩn bị một subset của queries từ dataset."""
        all_queries = []
        categories = [
            d
            for d in os.listdir(self.dataset_root)
            if os.path.isdir(os.path.join(self.dataset_root, d))
        ]

        for cat in categories:
            cat_path = os.path.join(self.dataset_root, cat)
            files = [
                f
                for f in os.listdir(cat_path)
                if f.lower().endswith((".png", ".jpg", ".jpeg"))
            ]

            if len(files) < 5:
                continue

            # Lấy mẫu từ category này
            num_to_select = min(len(files), max(5, int(len(files) * 0.5)))
            rng = random.Random(42)
            selected_files = rng.sample(files, num_to_select)

            label = cat.replace("_processed", "")

            for f in selected_files:
                img_path = os.path.join(cat_path, f)
                try:
                    img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
                    if img is None:
                        continue
                    feats = self.feature_extractor.execute(img)
                    if not self._validate_features(feats):
                        continue
                    all_queries.append(
                        {"path": img_path, "label": label, "features": feats}
                    )
                except Exception as e:
                    logger.error(f"Error processing image {img_path}: {e}")

        # Lấy subset ngẫu nhiên
        if len(all_queries) > subset_size:
            rng = random.Random(42)
            all_queries = rng.sample(all_queries, subset_size)

        return all_queries

    def _evaluate_single_feature(
        self,
        queries: List[Dict],
        weights: Dict[str, float],
        top_k: int = 5,
    ) -> float:
        """Tính mAP cho một feature cụ thể."""
        aps = []

        for i, q in enumerate(queries):
            distances = []

            for j, train_q in enumerate(queries):
                if i == j:  # Skip self
                    continue

                # Calculate weighted distance (chỉ dùng feature được chỉ định)
                weighted_dist = 0.0
                valid_features = 0

                for key, weight in weights.items():
                    if weight < 1e-6:
                        continue

                    if key not in q["features"] or key not in train_q["features"]:
                        continue

                    query_vec = np.array(q["features"][key], dtype=np.float64)
                    train_vec = np.array(train_q["features"][key], dtype=np.float64)

                    if len(query_vec) == 0 or len(train_vec) == 0:
                        continue

                    dist_contribution = weight * cosine_distance(query_vec, train_vec)
                    weighted_dist += dist_contribution
                    valid_features += weight

                if valid_features > 1e-6:
                    weighted_dist = weighted_dist / valid_features
                else:
                    weighted_dist = float("inf")

                distances.append((weighted_dist, train_q["label"], train_q["path"]))

            # Sort by distance
            distances.sort(key=lambda x: x[0])

            # Filter results
            filtered_results = [
                {"fruit_name": label, "filepath": path}
                for dist, label, path in distances
                if dist != float("inf")
            ][:top_k]

            # Calculate AP
            if filtered_results:
                aps.append(self._calculate_ap(filtered_results, q["label"], top_k))
            else:
                aps.append(0.0)

        return np.mean(aps) if aps else 0.0

    def _validate_features(self, features: Dict[str, List[float]]) -> bool:
        """Kiểm tra features hợp lệ."""
        if not features or not isinstance(features, dict):
            return False

        for key, vec in features.items():
            if not isinstance(vec, (list, np.ndarray)):
                return False
            vec_arr = np.array(vec)
            if (
                len(vec_arr) == 0
                or np.all(np.isnan(vec_arr))
                or np.all(np.isinf(vec_arr))
            ):
                return False

        return True

    def _calculate_ap(self, results, expected_label, k) -> float:
        """Tính Average Precision."""
        if not results:
            return 0.0

        query_label = str(expected_label).strip().lower()

        hits = 0
        sum_precision = 0.0
        total_relevant = sum(
            1
            for r in results
            if str(r.get("fruit_name", "")).strip().lower() == query_label
        )

        if total_relevant == 0:
            return 0.0

        for i, r in enumerate(results[:k]):
            res_label = str(r.get("fruit_name", "")).strip().lower()
            if res_label == query_label:
                hits += 1
                precision_at_i = hits / (i + 1)
                sum_precision += precision_at_i

        ap = sum_precision / total_relevant
        return min(ap, 1.0)
