import os
import cv2
import random
import time
from typing import Dict, List

from domain.constants import FEATURE_KEYS
from infrastructure.helper import get_weights
import numpy as np


class EvaluateTestDatasetUseCase:
    def __init__(
        self, feature_repo, feature_extractor, background_remover, dataset_root: str
    ):
        self.feature_repo = feature_repo
        self.feature_extractor = feature_extractor
        self.background_remover = background_remover
        self.dataset_root = dataset_root

    def execute(self, sample_size: int = 50, top_k: int = 5) -> Dict:
        """Đánh giá test set: precision@k, recall@k, mAP@k, top-1/k accuracy + confusion matrix."""
        queries = self._prepare_queries(sample_size)
        if not queries:
            return {"error": "No test images found for evaluation."}

        weights = get_weights()
        db_counts = self.feature_repo.count_per_fruit()
        # Chuẩn hoá key về lowercase để khớp với label đã chuẩn hoá
        db_counts_norm = {k.strip().lower(): v for k, v in db_counts.items()}
        all_labels = sorted(db_counts_norm.keys())

        per_fruit_records: Dict[str, List[Dict]] = {label: [] for label in all_labels}
        confusion_counts: Dict[str, Dict[str, int]] = {
            true_label: {pred_label: 0 for pred_label in all_labels}
            for true_label in all_labels
        }
        sample_results = []

        for query in queries:
            true_label = query["label"].strip().lower()
            if true_label not in per_fruit_records:
                per_fruit_records[true_label] = []
                confusion_counts[true_label] = {l: 0 for l in all_labels}

            start_search = time.time()
            results = self.feature_repo.search_similar(
                query["features"], weights, limit=top_k
            )
            search_time_ms = (time.time() - start_search) * 1000

            pred_labels = [r["fruit_name"].strip().lower() for r in results[:top_k]]

            # Đếm cho confusion matrix (top-k aggregated)
            for pred in pred_labels:
                if pred not in confusion_counts[true_label]:
                    confusion_counts[true_label][pred] = 0
                confusion_counts[true_label][pred] += 1

            hits = sum(1 for p in pred_labels if p == true_label)
            relevant_total = db_counts_norm.get(true_label, 0)

            precision_at_k = hits / top_k if top_k > 0 else 0.0
            recall_at_k = hits / relevant_total if relevant_total > 0 else 0.0
            top1_correct = 1 if pred_labels and pred_labels[0] == true_label else 0
            topk_correct = 1 if hits > 0 else 0
            ap_at_k = self._average_precision_at_k(pred_labels, true_label, top_k)

            per_fruit_records[true_label].append(
                {
                    "precision_at_k": precision_at_k,
                    "recall_at_k": recall_at_k,
                    "ap_at_k": ap_at_k,
                    "top1_correct": top1_correct,
                    "topk_correct": topk_correct,
                    "search_time_ms": search_time_ms,
                }
            )

            if len(sample_results) < 5:
                sample_results.append(
                    {
                        "query_file": query["relative_path"],
                        "label": query["label"],
                        "top_results": [
                            {
                                "filename": r["filename"],
                                "fruit_name": r["fruit_name"],
                                "similarity": r["similarity"],
                                "distance": r["distance"],
                            }
                            for r in results[:top_k]
                        ],
                    }
                )

        per_fruit_metrics = self._aggregate_per_fruit(per_fruit_records)
        global_metrics = self._aggregate_global(per_fruit_records)
        confusion_matrix = self._build_confusion_matrix(
            confusion_counts, per_fruit_records, top_k
        )

        return {
            "status": "success",
            "top_k": top_k,
            "global_metrics": global_metrics,
            "per_fruit_metrics": per_fruit_metrics,
            "confusion_matrix": confusion_matrix,
            "sample_results": sample_results,
        }

    def _aggregate_per_fruit(self, records: Dict[str, List[Dict]]) -> Dict:
        out = {}
        for label, items in records.items():
            if not items:
                continue
            arr = lambda key: np.array([it[key] for it in items], dtype=np.float64)
            precision = float(arr("precision_at_k").mean())
            recall = float(arr("recall_at_k").mean())
            f1 = (
                2 * precision * recall / (precision + recall)
                if (precision + recall) > 0
                else 0.0
            )
            out[label] = {
                "queries_count": len(items),
                "precision_at_k": round(precision, 4),
                "recall_at_k": round(recall, 4),
                "f1": round(f1, 4),
                "mAP_at_k": round(float(arr("ap_at_k").mean()), 4),
                "top1_accuracy": round(float(arr("top1_correct").mean()), 4),
                "topk_accuracy": round(float(arr("topk_correct").mean()), 4),
                "mean_search_time_ms": round(float(arr("search_time_ms").mean()), 2),
            }
        return out

    def _aggregate_global(self, records: Dict[str, List[Dict]]) -> Dict:
        all_items = [it for items in records.values() for it in items]
        if not all_items:
            return {}
        arr = lambda key: np.array([it[key] for it in all_items], dtype=np.float64)
        precision = float(arr("precision_at_k").mean())
        recall = float(arr("recall_at_k").mean())
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )
        return {
            "queries_count": len(all_items),
            "mean_precision_at_k": round(precision, 4),
            "mean_recall_at_k": round(recall, 4),
            "mean_f1": round(f1, 4),
            "mAP_at_k": round(float(arr("ap_at_k").mean()), 4),
            "mean_top1_accuracy": round(float(arr("top1_correct").mean()), 4),
            "mean_topk_accuracy": round(float(arr("topk_correct").mean()), 4),
            "mean_search_time_ms": round(float(arr("search_time_ms").mean()), 2),
        }

    def _build_confusion_matrix(
        self,
        confusion_counts: Dict[str, Dict[str, int]],
        records: Dict[str, List[Dict]],
        top_k: int,
    ) -> Dict:
        """Mỗi cell = % slot trong top-K trên mọi query của true_label được dự đoán là pred_label.
        Hàng tổng = 100% (tất cả slot top-K được phân bổ cho các pred_label)."""
        all_labels = sorted(confusion_counts.keys())
        matrix = []
        for true_label in all_labels:
            queries_count = len(records.get(true_label, []))
            denom = queries_count * top_k
            row = {"true_label": true_label, "queries_count": queries_count, "cells": {}}
            for pred_label in all_labels:
                count = confusion_counts[true_label].get(pred_label, 0)
                pct = (count / denom) if denom > 0 else 0.0
                row["cells"][pred_label] = {
                    "count": count,
                    "percent": round(pct, 4),
                }
            matrix.append(row)
        return {"labels": all_labels, "rows": matrix}

    def _average_precision_at_k(
        self, pred_labels: List[str], true_label: str, k: int
    ) -> float:
        if not pred_labels:
            return 0.0
        hits = 0
        sum_precision = 0.0
        for i, pred in enumerate(pred_labels[:k]):
            if pred == true_label:
                hits += 1
                sum_precision += hits / (i + 1)
        if hits == 0:
            return 0.0
        return sum_precision / hits

    def _prepare_queries(self, sample_size: int) -> List[Dict]:
        categories = [
            d
            for d in os.listdir(self.dataset_root)
            if os.path.isdir(os.path.join(self.dataset_root, d))
        ]

        queries = []
        for category_dir in sorted(categories):
            category_path = os.path.join(self.dataset_root, category_dir)
            image_files = [
                f
                for f in sorted(os.listdir(category_path))
                if f.lower().endswith((".png", ".jpg", ".jpeg"))
            ]
            for filename in image_files:
                relative_path = os.path.join(category_dir, filename)
                image_path = os.path.join(category_path, filename)
                image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
                if image is None:
                    continue
                features = self.feature_extractor.execute(image)
                if not self._validate_features(features):
                    continue
                queries.append(
                    {
                        "label": category_dir.replace("_processed", ""),
                        "features": features,
                        "relative_path": relative_path,
                    }
                )

        if len(queries) > sample_size:
            random.Random(42).shuffle(queries)
            queries = queries[:sample_size]

        return queries

    def _validate_features(self, features: Dict[str, List[float]]) -> bool:
        if not isinstance(features, dict):
            return False
        for key in FEATURE_KEYS:
            vec = features.get(key)
            if vec is None or len(vec) == 0:
                return False
        return True
