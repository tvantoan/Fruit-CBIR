import cv2
import numpy as np
from flask import session

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
    session['last_features'] = features_dict

def get_features() -> dict | None:
    """Lấy vector đã lưu từ session."""
    if 'last_features' not in session:
        print("No features found in session.")
        return None
    return session.get('last_features')

def clear():
    """Xóa dữ liệu khi phiên làm việc kết thúc."""
    session.pop('last_features', None)