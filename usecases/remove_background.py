import os
import numpy as np
import cv2
from rembg import remove
from PIL import Image
from domain.usecase import IRemoveBackground

class BackgroundRemover(IRemoveBackground):
    def __init__(self, target_size: int = 256):
        self.target_size = target_size

    def execute(self, image_data: np.ndarray) -> np.ndarray:
            if image_data is None:
                raise ValueError("Không thể đọc ảnh từ dữ liệu đầu vào")

            res_rgba = remove(image_data)

            alpha = res_rgba[:, :, 3]
            coords = cv2.findNonZero(alpha)

            if coords is None:

                return cv2.cvtColor(res_rgba, cv2.COLOR_RGBA2BGR)

            x, y, w, h = cv2.boundingRect(coords)
            fruit_crop = res_rgba[y:y+h, x:x+w]

            scale = self.target_size / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            fruit_resized = cv2.resize(fruit_crop, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

            final_canvas = np.zeros((self.target_size, self.target_size, 3), dtype=np.uint8)

            off_x = (self.target_size - new_w) // 2
            off_y = (self.target_size - new_h) // 2
            final_canvas[off_y:off_y+new_h, off_x:off_x+new_w] = fruit_resized[:, :, :3]

            return final_canvas