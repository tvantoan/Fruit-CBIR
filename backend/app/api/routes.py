import os
import time
import uuid
from flask import request, jsonify, current_app
from PIL import Image

from app.api import api_bp
from app.api.search_interface import extract_features, search_similar
from database.db_manager import insert_image, get_image, get_stats as db_get_stats, log_query


def allowed_file(filename):
    allowed = current_app.config['ALLOWED_EXTENSIONS']
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


@api_bp.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed. Use png, jpg, or jpeg'}), 400

    ext = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    upload_folder = current_app.config['UPLOAD_FOLDER']
    filepath = os.path.join(upload_folder, unique_filename)
    file.save(filepath)

    img = Image.open(filepath)
    width, height = img.size
    file_size_kb = os.path.getsize(filepath) / 1024

    image_id = insert_image(
        filename=unique_filename,
        filepath=f"uploads/{unique_filename}",
        fruit_label="unknown",
        width=width,
        height=height,
        file_size_kb=round(file_size_kb, 2)
    )

    # Integration point: Member B's feature extraction
    extract_features(image_id, filepath)

    return jsonify({
        'image_id': image_id,
        'filename': unique_filename,
        'filepath': f"/static/uploads/{unique_filename}",
        'width': width,
        'height': height,
    }), 201


@api_bp.route('/search', methods=['GET'])
def search():
    image_id = request.args.get('image_id', type=int)
    if not image_id:
        return jsonify({'error': 'image_id parameter is required'}), 400

    query_image = get_image(image_id)
    if not query_image:
        return jsonify({'error': 'Image not found'}), 404

    start_time = time.time()
    results = search_similar(image_id, top_k=5)
    query_time_ms = round((time.time() - start_time) * 1000, 2)

    # Add static path for frontend to display images
    for r in results:
        r['image_url'] = f"/static/{r['filepath']}"

    # Log query
    result_ids = [r['image_id'] for r in results]
    distances = [r['distance'] for r in results]
    log_query(query_image['filepath'], result_ids, distances, query_time_ms)

    # Serialize query_image (datetime not JSON-serializable)
    query_data = dict(query_image)
    query_data['date_added'] = str(query_data.get('date_added', ''))
    query_data['image_url'] = f"/static/{query_data['filepath']}"

    return jsonify({
        'query_image': query_data,
        'results': results,
        'query_time_ms': query_time_ms,
    })


@api_bp.route('/images/<int:image_id>', methods=['GET'])
def get_image_detail(image_id):
    image = get_image(image_id)
    if not image:
        return jsonify({'error': 'Image not found'}), 404

    image_data = dict(image)
    image_data['date_added'] = str(image_data.get('date_added', ''))
    image_data['image_url'] = f"/static/{image_data['filepath']}"

    return jsonify(image_data)


@api_bp.route('/stats', methods=['GET'])
def stats():
    return jsonify(db_get_stats())
