import cv2
import numpy as np
import json
import os
from flask import session
from domain.constants import FEATURE_KEYS


def open_image(file_source):
    """Đọc ảnh từ đường dẫn hoặc từ file stream."""
    if isinstance(file_source, str):
        return cv2.imread(file_source)
    img_bytes = np.frombuffer(file_source.read(), np.uint8)
    return cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)


def resize_standard(image, size=(224, 224)):
    return cv2.resize(image, size)


def save_features(features_dict: dict):
    """Lưu kết quả trích xuất vector vào session."""
    session["last_features"] = features_dict


def get_features() -> dict | None:
    """Lấy vector đã lưu từ session."""
    if "last_features" not in session:
        print("No features found in session.")
        return None
    return session.get("last_features")


def clear():
    """Xóa dữ liệu khi phiên làm việc kết thúc."""
    session.pop("last_features", None)


def get_weights():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "persistence", "optimized_weights.json")

    # Khởi tạo bộ trọng số bằng 0
    zero_weights = {key: 0.0 for key in FEATURE_KEYS}

    if not os.path.exists(file_path):
        print(
            f"WARNING: Optimized weights file not found at {file_path}. All weights set to 0."
        )
        return zero_weights

    try:
        with open(file_path, "r") as f:
            weights = json.load(f)

        # Kiểm tra xem có đủ các key cần thiết không
        final_weights = {}
        for key in FEATURE_KEYS:
            if key in weights:
                final_weights[key] = float(weights[key])
            else:
                print(f"NOTICE: Key '{key}' missing in JSON. Setting to 0.")
                final_weights[key] = 0.0

        return final_weights

    except (json.JSONDecodeError, ValueError, IOError) as e:
        print(f"ERROR: Could not load optimized weights: {e}. Resetting all to 0.")
        return zero_weights


def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    """Normalize feature weights so their sum equals 1."""
    total = sum(weights.values())
    if total <= 0.0:
        return {key: 0.0 for key in FEATURE_KEYS}
    return {key: float(weights.get(key, 0.0)) / total for key in FEATURE_KEYS}


def cosine_similarity(vec1, vec2) -> float:
    """Cosine similarity between two feature vectors."""
    a = np.array(vec1, dtype=np.float64)
    b = np.array(vec2, dtype=np.float64)
    if a.size == 0 or b.size == 0:
        return 0.0
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a < 1e-10 or norm_b < 1e-10:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def cosine_distance(vec1, vec2) -> float:
    """Cosine distance computed as 1 - cosine similarity."""
    return 1.0 - cosine_similarity(vec1, vec2)
