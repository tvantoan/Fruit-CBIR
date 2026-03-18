"""
Integration contract for Member B's search engine.

Member B: Replace the mock implementations below with real feature extraction
and search logic. This is the ONLY file you need to modify to connect
the algorithm layer to the web layer.
"""
import random
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from database.db_manager import get_random_images


def extract_features(image_id: int, filepath: str) -> None:
    """
    Extract all feature vectors from the image and store in DB.

    Member B: Implement this by:
    1. Loading the image from filepath with cv2.imread
    2. Running all feature extractors (color, gabor, edge, HOG,
       color_moments, hu_moments, glcm, lbp)
    3. Calling db_manager.insert_feature() for each feature type

    This is called automatically after each image upload.
    """
    pass  # TODO: Member B implements


def search_similar(image_id: int, top_k: int = 5) -> list[dict]:
    """
    Find top_k most similar images to the given image_id.

    Returns list of dicts:
    [
        {
            "image_id": int,
            "filename": str,
            "filepath": str,
            "fruit_label": str,
            "similarity": float,  # 0.0 to 1.0
            "distance": float,
            "feature_distances": {
                "color": float,
                "texture": float,
                "shape": float,
            }
        },
        ...
    ]

    Member B: Implement this by:
    1. Get features for image_id from DB
    2. Use KD-Tree/FAISS index to find nearest neighbors
    3. Return top_k results with distances
    """
    # MOCK: Return random images with fake scores
    mock_results = get_random_images(top_k)
    results = []
    for i, row in enumerate(mock_results):
        similarity = round(random.uniform(0.70, 0.99), 3)
        results.append({
            'image_id': row['image_id'],
            'filename': row['filename'],
            'filepath': row['filepath'],
            'fruit_label': row['fruit_label'],
            'similarity': similarity,
            'distance': round(1 - similarity, 3),
            'feature_distances': {
                'color': round(random.uniform(0.01, 0.3), 3),
                'texture': round(random.uniform(0.01, 0.3), 3),
                'shape': round(random.uniform(0.01, 0.3), 3),
            }
        })
    return sorted(results, key=lambda x: x['distance'])
