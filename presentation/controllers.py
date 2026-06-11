"""Presentation layer - HTTP endpoint handlers."""

import os
import time
import threading
import numpy as np
import cv2
from flask import Blueprint, jsonify, request, send_from_directory

from domain.constants import DATA_PATH, SERVED_IMAGE_API, SERVED_IMAGE_ROUTE
from domain.repositories import IImageRepository, IFeatureRepository, IFruitRepository
from domain.usecase import IFeatureExtractor, IRemoveBackground
from infrastructure.repositories import (
    FeatureRepository,
    FruitRepository,
    ImageRepository,
)
from usecases.feature_extractor import FeatureExtractor
from usecases.optimize_weights import OptimizeWeightsUseCase
from usecases.remove_background import BackgroundRemover
from usecases.search_images import SearchImagesUseCase
from usecases.evaluate_features import EvaluateFeaturesUseCase
from usecases.evaluate_test_dataset import EvaluateTestDatasetUseCase

api_bp = Blueprint("api", __name__)


DATASET_ROOT = os.path.join(
    os.path.dirname(__file__), "..", "static", "Fruits_data_processed"
)
TEST_DATA_ROOT = os.path.join(
    os.path.dirname(__file__), "..", "static", "Fruits_data_test"
)

optimization_lock = threading.Lock()
optimization_thread = None
optimization_status = {
    "status": "idle",
    "current_trial": 0,
    "total_trials": 0,
    "last_trial_mAP": None,
    "last_trial_weights": {},
    "best_mAP": None,
    "best_weights": {},
    "started_at": None,
    "ended_at": None,
    "error": None,
}


def _reset_optimization_status(total_trials: int):
    with optimization_lock:
        optimization_status.update(
            {
                "status": "starting",
                "current_trial": 0,
                "total_trials": total_trials,
                "last_trial_mAP": None,
                "last_trial_weights": {},
                "best_mAP": None,
                "best_weights": {},
                "started_at": time.time(),
                "ended_at": None,
                "error": None,
            }
        )


def _update_optimization_status(updates: dict):
    with optimization_lock:
        optimization_status.update(updates)


def _get_optimization_status():
    with optimization_lock:
        return dict(optimization_status)


def _run_optimization(n_trials: int):
    try:
        # Import Flask app để có app context
        from app import app
        import logging

        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        logger.info("Starting optimization with %d trials", n_trials)

        with app.app_context():
            logger.info("Entered Flask app context")

            use_case = OptimizeWeightsUseCase(
                feature_repo=FeatureRepository(),
                feature_extractor=FeatureExtractor(),
                dataset_root=DATASET_ROOT,
            )
            logger.info("Created OptimizeWeightsUseCase")

            def progress_callback(update):
                logger.info("Progress update: %s", update)
                _update_optimization_status(update)

            result = use_case.execute(
                n_trials=n_trials,
                progress_callback=progress_callback,
            )
            logger.info("Optimization completed: %s", result)

            _update_optimization_status(
                {
                    "status": "finished",
                    "best_mAP": result.get("best_mAP"),
                    "best_weights": result.get("best_weights", {}),
                    "ended_at": time.time(),
                }
            )
    except Exception as exc:
        import traceback

        error_msg = f"{str(exc)}\n{traceback.format_exc()}"
        print(f"Optimization failed: {error_msg}")  # Also print to console
        _update_optimization_status(
            {
                "status": "error",
                "error": error_msg,
                "ended_at": time.time(),
            }
        )


def _start_optimization(n_trials: int):
    global optimization_thread
    if optimization_thread and optimization_thread.is_alive():
        return False
    _reset_optimization_status(n_trials)
    optimization_thread = threading.Thread(
        target=_run_optimization,
        args=(n_trials,),
        daemon=True,
    )
    optimization_thread.start()
    return True


def _get_search_use_case() -> SearchImagesUseCase:
    """Khởi tạo và lắp ghép SearchImagesUseCase với các dependencies thực tế."""
    return SearchImagesUseCase(
        image_repo=ImageRepository(),
        feature_repo=FeatureRepository(),
        feature_extractor=FeatureExtractor(),
        fruit_repo=FruitRepository(),
        background_remover=BackgroundRemover(),
    )


@api_bp.route("/search", methods=["POST"])
def search():
    """Search for similar images using an uploaded image file."""
    if "image" not in request.files:
        return jsonify({"error": "No image file provided in request"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    try:
        start_time = time.time()

        img_bytes = np.frombuffer(file.read(), np.uint8)
        image = cv2.imdecode(img_bytes, cv2.IMREAD_UNCHANGED)

        if image is None:
            return jsonify({"error": "Invalid image format"}), 400

        use_case = _get_search_use_case()

        removed_background = use_case.background_remover.execute(image)
        search_results = use_case.execute(image_data=removed_background)

        query_time_ms = round((time.time() - start_time) * 1000, 2)

        return jsonify(
            {
                "status": "success",
                "query_stats": {
                    "query_time_ms": query_time_ms,
                },
                "results": search_results,
            }
        )

    except Exception as exc:
        import traceback

        traceback.print_exc()
        return jsonify({"error": "Search failed, please try again later"}), 500


@api_bp.route("/fruits", methods=["GET"])
def get_fruits():
    fruit_repo = FruitRepository()
    image_repo = ImageRepository()

    fruits = fruit_repo.get_all()
    data = []
    for fruit in fruits:
        sample_image = image_repo.get_sample_by_fruit_id(fruit.fruit_id)
        data.append(
            {
                "fruit_id": fruit.fruit_id,
                "name": fruit.name,
                "description": fruit.description,
                "sample_image_url": (
                    f"{SERVED_IMAGE_API}{sample_image.filepath}"
                    if sample_image
                    else None
                ),
            }
        )

    return jsonify({"fruits": data})


@api_bp.route(f"{SERVED_IMAGE_ROUTE}<path:filename>")
def serve_image(filename):
    return send_from_directory(f"{os.path.abspath(DATA_PATH)}", filename)


@api_bp.route("/admin/optimize", methods=["GET"])
def get_optimization_status():
    return jsonify(_get_optimization_status())


@api_bp.route("/admin/optimize", methods=["POST"])
def start_optimization():
    request_data = request.get_json(silent=True) or {}
    n_trials = request_data.get("n_trials")
    if n_trials is None:
        n_trials = request.args.get("n_trials", default=100, type=int)

    if n_trials is None or n_trials <= 0:
        return jsonify({"error": "Invalid n_trials value"}), 400

    if not _start_optimization(n_trials):
        return jsonify({"error": "Optimization is already running"}), 409

    return jsonify(
        {
            "status": "started",
            "optimization_status": _get_optimization_status(),
        }
    )


@api_bp.route("/admin/evaluate-features", methods=["GET"])
def evaluate_features():
    """Evaluate mAP for each individual feature on a dataset subset."""
    try:
        subset_size = request.args.get("subset_size", default=100, type=int)
        if subset_size <= 0:
            return jsonify({"error": "Invalid subset_size"}), 400

        use_case = EvaluateFeaturesUseCase(
            feature_extractor=FeatureExtractor(),
            dataset_root=DATASET_ROOT,
        )

        results = use_case.execute(subset_size=subset_size)

        if "error" in results:
            return jsonify({"error": results["error"]}), 500

        return jsonify(
            {"status": "success", "subset_size": subset_size, "feature_mAPs": results}
        )

    except Exception as exc:
        import traceback

        traceback.print_exc()
        return jsonify({"error": "Feature evaluation failed"}), 500


@api_bp.route("/admin/test-evaluation", methods=["GET"])
def evaluate_test_dataset():
    """Evaluate test dataset and return per-fruit and global metrics including precision, recall, f1, top-1/5 accuracy, and search time."""
    try:
        sample_size = request.args.get("sample_size", default=50, type=int)
        top_k = request.args.get("top_k", default=5, type=int)
        if sample_size <= 0 or top_k <= 0:
            return jsonify({"error": "Invalid sample_size or top_k"}), 400

        use_case = EvaluateTestDatasetUseCase(
            feature_repo=FeatureRepository(),
            feature_extractor=FeatureExtractor(),
            background_remover=BackgroundRemover(),
            dataset_root=TEST_DATA_ROOT,
        )

        results = use_case.execute(sample_size=sample_size, top_k=top_k)
        if "error" in results:
            return jsonify({"error": results["error"]}), 500

        return jsonify(results)

    except Exception as exc:
        import traceback

        traceback.print_exc()
        return jsonify({"error": "Test dataset evaluation failed"}), 500
