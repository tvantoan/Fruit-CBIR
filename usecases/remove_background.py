import os
import numpy as np
import cv2
from rembg import remove
from PIL import Image
from domain.usecase import IRemoveBackground

class BackgroundRemover(IRemoveBackground):
    def __init__(self, target_size: int = 224):
        self.target_size = target_size

    def execute(self, image_data: np.ndarray, target_size: int = 224) -> np.ndarray:
        """
        Quy trình nhất quán: Tách nền -> Crop sát -> Resize & Pad (4 kênh)
        """
        if image_data is None:
            return None

        # 1. Tách nền (vẫn giữ nguyên 4 kênh RGBA)
        res_rgba = remove(image_data)
        res_rgba = cv2.cvtColor(res_rgba, cv2.COLOR_RGBA2BGRA)
        alpha = res_rgba[:, :, 3]

        # 2. Tìm vùng chứa đối tượng (Kết hợp alpha > 0 và boundingRect)
        # Dùng np.where để lọc nhiễu alpha nếu cần (ví dụ alpha > 10)
        coords = cv2.findNonZero(alpha)

        if coords is None:
            # Nếu không tìm thấy đối tượng, trả về khung trống trong suốt
            return np.zeros((target_size, target_size, 4), dtype=np.uint8)

        # Lấy bounding box sát nhất
        x, y, w, h = cv2.boundingRect(coords)
        fruit_crop = res_rgba[y:y+h, x:x+w]

        # 3. Tính toán tỷ lệ và Resize MỘT LẦN duy nhất
        # Việc resize một lần giúp tránh mất mát chi tiết (aliasing)
        scale = target_size / max(h, w)
        new_w, new_h = int(w * scale), int(h * scale)

        # Dùng INTER_LANCZOS4 để có chất lượng ảnh tốt nhất cho đặc trưng màu/hình dạng
        fruit_resized = cv2.resize(fruit_crop, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

        # 4. Tạo canvas 4 kênh (Trong suốt hoàn toàn)
        final_canvas = np.zeros((target_size, target_size, 4), dtype=np.uint8)

        # Đưa ảnh vào chính giữa
        off_x = (target_size - new_w) // 2
        off_y = (target_size - new_h) // 2
        final_canvas[off_y:off_y+new_h, off_x:off_x+new_w] = fruit_resized

        return final_canvas