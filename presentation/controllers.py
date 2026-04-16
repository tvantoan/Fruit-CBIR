"""Presentation layer - HTTP endpoint handlers."""

import os
import time
from flask import Blueprint, jsonify, request, send_from_directory

from domain.constants import DATA_PATH, SERVED_IMAGE_API, SERVED_IMAGE_ROUTE
from domain.repositories import IImageRepository, IFeatureRepository, IFruitRepository
from domain.usecase import IFeatureExtractor, IRemoveBackground
from infrastructure.repositories import FeatureRepository, FruitRepository, ImageRepository
from usecases.feature_extractor import FeatureExtractor
from usecases.remove_background import BackgroundRemover
from usecases.search_images import SearchImagesUseCase

api_bp = Blueprint('api', __name__)


DATASET_ROOT = os.path.join(os.path.dirname(__file__), '..', 'static', 'Fruits_data_processed')


def _get_search_use_case() -> SearchImagesUseCase:
    """Khởi tạo và lắp ghép SearchImagesUseCase với các dependencies thực tế."""
    return SearchImagesUseCase(
        image_repo=ImageRepository(),
        feature_repo=FeatureRepository(),
        feature_extractor=FeatureExtractor(),
        fruit_repo=FruitRepository(),
        background_remover=BackgroundRemover()
    )


import time
import numpy as np
import cv2
from flask import request, jsonify

@api_bp.route('/search', methods=['POST'])
def search():
    """Search for similar images using an uploaded image file."""
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided in request'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    top_k = request.form.get('top_k', default=5, type=int)

    weights = {
        'color': request.form.get('weight_color', default=0.7, type=float),
        'texture': request.form.get('weight_texture', default=0.2, type=float),
        'shape': request.form.get('weight_shape', default=0.1, type=float)
    }

    try:
        start_time = time.time()

        img_bytes = np.frombuffer(file.read(), np.uint8)
        image = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)

        if image is None:
            return jsonify({'error': 'Invalid image format'}), 400

        use_case = _get_search_use_case()

        removed_background = use_case.background_remover.execute(image)
        search_results = use_case.execute(image_data=removed_background, weights=weights)

        query_time_ms = round((time.time() - start_time) * 1000, 2)


        return jsonify({
            'status': 'success',
            'query_stats': {
                'query_time_ms': query_time_ms,
                'top_k': top_k,
                'weights_applied': weights
            },
            'results': search_results
        })

    except Exception as exc:
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Search failed, please try again later'}), 500

@api_bp.route('/fruits', methods=['GET'])

def get_fruits():
    fruit_repo = FruitRepository()
    image_repo = ImageRepository()

    fruits = fruit_repo.get_all()
    data = []
    for fruit in fruits:
        sample_image = image_repo.get_sample_by_fruit_id(fruit.fruit_id)
        data.append({
            'fruit_id': fruit.fruit_id,
            'name': fruit.name,
            'description': fruit.description,
            'sample_image_url': f"{SERVED_IMAGE_API}{sample_image.filepath}" if sample_image else None
        })

    return jsonify({'fruits': data})

@api_bp.route(f"{SERVED_IMAGE_ROUTE}<path:filename>")
def serve_image(filename):
    return send_from_directory(f'{os.path.abspath(DATA_PATH)}', filename)