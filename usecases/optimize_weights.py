import os
from random import sample
import cv2
import optuna
import numpy as np
import logging
import random
from typing import Dict, List, Any, Callable, Optional

from domain.constants import FEATURE_KEYS
from infrastructure.helper import cosine_distance, normalize_weights

logger = logging.getLogger(__name__)

OPTIMIZED_WEIGHTS_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "infrastructure",
    "persistence",
    "optimized_weights.json",
)


class OptimizeWeightsUseCase:
    def __init__(self, feature_repo, feature_extractor, dataset_root: str):
        self.feature_repo = feature_repo
        self.feature_extractor = feature_extractor
        self.dataset_root = dataset_root

    def execute(
        self,
        n_trials: int = 100,
        top_k: int = 5,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        logger.info(
            f"Starting optimization with {n_trials} trials, dataset_root={self.dataset_root}"
        )

        train_queries, val_queries = self._prepare_queries()

        if not train_queries or not val_queries:
            error_msg = f"Insufficient images: train={len(train_queries)}, val={len(val_queries)}"
            logger.error(error_msg)
            return {"error": error_msg}

        logger.info(
            f"Dataset ready: {len(train_queries)} train queries, {len(val_queries)} validation queries"
        )

        def objective(trial):
            weights = {key: trial.suggest_float(key, 0.0, 1.0) for key in FEATURE_KEYS}
            weights = normalize_weights(weights)
            mAP = self._evaluate(train_queries, val_queries, weights, top_k)
            logger.debug(f"Trial {trial.number}: weights={weights}, mAP={mAP}")
            return mAP

        study = optuna.create_study(
            direction="maximize", sampler=optuna.samplers.TPESampler(seed=42)
        )

        def _trial_callback(study_obj, trial):
            if not progress_callback:
                return

            normalized_trial_weights = normalize_weights(trial.params)
            best_weights = (
                normalize_weights(study_obj.best_params)
                if study_obj.best_params
                else {}
            )
            progress_callback(
                {
                    "current_trial": trial.number + 1,
                    "total_trials": n_trials,
                    "last_trial_mAP": trial.value,
                    "last_trial_weights": normalized_trial_weights,
                    "best_mAP": study_obj.best_value,
                    "best_weights": best_weights,
                    "status": "running",
                }
            )

        logger.info("Starting optimization study")
        study.optimize(objective, n_trials=n_trials, callbacks=[_trial_callback])

        best_weights = normalize_weights(study.best_params)
        logger.info(f"Optimization completed. Best mAP: {study.best_value}")
        logger.info(f"Best weights: {best_weights}")

        # Save to file
        try:
            optimized_weights_path = OPTIMIZED_WEIGHTS_PATH
            os.makedirs(os.path.dirname(optimized_weights_path), exist_ok=True)
            with open(optimized_weights_path, "w") as f:
                import json

                json.dump(best_weights, f, indent=2)
            logger.info(f"Saved optimized weights to {optimized_weights_path}")
        except Exception as e:
            logger.error(f"Failed to save optimized weights: {e}")

        return {
            "best_mAP": study.best_value,
            "best_weights": best_weights,
            "trials": n_trials,
        }

    def _prepare_queries(self) -> tuple[List[Dict], List[Dict]]:
        """Quét thư mục để lấy ảnh mẫu và nhãn trực tiếp, chia thành train và validation."""
        train_queries = []
        val_queries = []
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
            rng = random.Random(42)

            num_to_select = min(len(files), max(10, int(len(files) * 0.05)))
            if len(files) < 5:
                continue

            random_files = rng.sample(files, num_to_select)
            n_train = max(1, int(len(random_files) * 0.7))
            train_files = rng.sample(random_files, n_train)
            val_files = [f for f in random_files if f not in train_files]

            label = cat.replace("_processed", "")

            # Train queries
            for f in train_files:
                img_path = os.path.join(cat_path, f)
                try:
                    img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
                    if img is None:
                        logger.warning(f"Failed to read image: {img_path}")
                        continue
                    feats = self.feature_extractor.execute(img)
                    if not self._validate_features(feats):
                        logger.warning(f"Invalid features for {img_path}")
                        continue
                    train_queries.append(
                        {"path": img_path, "label": label, "features": feats}
                    )
                except Exception as e:
                    logger.error(f"Error processing training image {img_path}: {e}")

            # Validation queries
            for f in val_files:
                img_path = os.path.join(cat_path, f)
                try:
                    img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
                    if img is None:
                        logger.warning(f"Failed to read image: {img_path}")
                        continue
                    feats = self.feature_extractor.execute(img)
                    if not self._validate_features(feats):
                        logger.warning(f"Invalid features for {img_path}")
                        continue
                    val_queries.append(
                        {"path": img_path, "label": label, "features": feats}
                    )
                except Exception as e:
                    logger.error(f"Error processing validation image {img_path}: {e}")

        logger.info(
            f"Prepared {len(train_queries)} train and {len(val_queries)} validation queries"
        )
        return train_queries, val_queries

    def _evaluate(
        self,
        train_queries: List[Dict],
        val_queries: List[Dict],
        weights: Dict,
        top_k: int,
    ) -> float:
        """Tính mAP dựa trên việc so khớp Label, sử dụng train_queries làm database."""
        aps = []

        for q in val_queries:
            distances = []

            for train_q in train_queries:
                # Calculate weighted cosine distance
                weighted_dist = 0.0
                valid_features = 0

                for key, weight in weights.items():
                    if weight < 1e-6:  # Skip near-zero weights
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

                # Normalize by total weight used
                if valid_features > 1e-6:
                    weighted_dist = weighted_dist / valid_features
                else:
                    weighted_dist = float("inf")

                distances.append((weighted_dist, train_q["label"], train_q["path"]))

            # Sort by distance (lower is better)
            distances.sort(key=lambda x: x[0])

            # Filter out the query image itself if it's in train set
            filtered_results = [
                {"fruit_name": label, "filepath": path}
                for dist, label, path in distances
                if path != q["path"] and dist != float("inf")
            ]

            # Calculate AP
            if filtered_results:
                aps.append(self._calculate_ap(filtered_results, q["label"], top_k))
            else:
                aps.append(0.0)

        return np.mean(aps) if aps else 0.0

    def _validate_features(self, features: Dict[str, List[float]]) -> bool:
        """Kiểm tra xem features có hợp lệ không."""
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
        """
        Tính Average Precision với label matching.
        AP = (sum of precision at each relevant position) / (total relevant items in results)
        """
        if not results:
            return 0.0

        # Normalize labels for comparison
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

        # Calculate precision at each position
        for i, r in enumerate(results[:k]):
            res_label = str(r.get("fruit_name", "")).strip().lower()
            if res_label == query_label:
                hits += 1
                # Precision at this position
                precision_at_i = hits / (i + 1)
                sum_precision += precision_at_i

        # AP = sum_precision / total_relevant items (not k)
        # This ensures AP is in [0, 1]
        ap = sum_precision / total_relevant
        return min(ap, 1.0)  # Ensure it's capped at 1
