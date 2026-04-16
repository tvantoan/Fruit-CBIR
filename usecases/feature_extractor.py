from __future__ import annotations
import os
import cv2
import numpy as np
from PIL import Image, ImageOps
from domain.usecase import IFeatureExtractor
from skimage.feature import local_binary_pattern
import math

class FeatureExtractor(IFeatureExtractor):

    def execute(self, image_data: np.ndarray) -> dict[str, list[float]]:
        """
        Nhận vào image_data là np.ndarray (BGR).
        Trả về dict chứa các vector đặc trưng đã được chuẩn hóa.
        """
        if not isinstance(image_data, np.ndarray):
            image_data = np.array(image_data)

        if image_data.dtype != np.uint8:
            image_data = image_data.astype(np.uint8)

        color_vec = self._build_color_vector(image_data)
        texture_vec = self._build_texture_vector(image_data)
        shape_vec = self._build_shape_vector(image_data)


        return {
            'color': color_vec,
            'texture': texture_vec,
            'shape': shape_vec,
        }

    def _build_color_vector(self, image: np.ndarray) -> list[float]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        _, mask_white = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
        _, mask_black = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY_INV)

        background_mask = cv2.bitwise_or(mask_white, mask_black)
        mask = cv2.bitwise_not(background_mask)

        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        hist = cv2.calcHist([hsv], [0, 1, 2], mask, [16, 4, 4], [0, 180, 0, 256, 0, 256])

        total_pixels = np.sum(hist)
        if total_pixels > 0:
            cv2.normalize(hist, hist, alpha=1.0, beta=0.0, norm_type=cv2.NORM_L2)
            return hist.flatten().tolist()
        else:
            return [1.0 / 256] * 256

    def _build_texture_vector(self, image: np.ndarray) -> list[float]:
        """Sử dụng LBP để lấy đặc trưng vân bề mặt (vỏ quả, thớ vải...)."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


        lbp = local_binary_pattern(gray, P=8, R=1, method="uniform")


        (hist, _) = np.histogram(lbp.ravel(), bins=10, range=(0, 10))


        hist = hist.astype("float")
        hist /= (hist.sum() + 1e-7)
        return hist.tolist()

    def _build_shape_vector(self, image: np.ndarray) -> list[float]:
        """Tính Hu Moments để lấy đặc trưng hình dạng (bất biến xoay/tỉ lệ)."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        moments = cv2.moments(thresh)
        hu = cv2.HuMoments(moments).flatten()

        hu_log = []
        for i in range(7):
            val = -1 * math.copysign(1.0, hu[i]) * math.log10(abs(hu[i]) + 1e-11)
            hu_log.append(val)
        return hu_log