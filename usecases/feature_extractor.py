from __future__ import annotations
import cv2
import numpy as np
from domain.constants import FEATURE_KEYS
from domain.usecase import IFeatureExtractor
from skimage.feature import local_binary_pattern, graycomatrix, graycoprops, hog
import math
import mahotas


class FeatureExtractor(IFeatureExtractor):

    def execute(self, image_data: np.ndarray) -> dict[str, list[float]]:
        if not isinstance(image_data, np.ndarray):
            image_data = np.array(image_data)
        if image_data.dtype != np.uint8:
            image_data = image_data.astype(np.uint8)

        bgr, mask = self._split_bgr_and_mask(image_data)

        return {
            key: getattr(self, f"_build_{key}_vector")(bgr, mask)
            for key in FEATURE_KEYS
        }

    def _split_bgr_and_mask(
        self, image: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """Tách BGR (3 kênh) và mask binary (uint8 0/255) từ ảnh đầu vào.

        - 4 kênh (BGRA): mask = alpha > 0
        - 3 kênh (BGR): mask = toàn bộ ảnh (255)
        """
        if image.ndim == 3 and image.shape[2] == 4:
            bgr = image[:, :, :3]
            mask = (image[:, :, 3] > 0).astype(np.uint8) * 255
        else:
            bgr = image if image.ndim == 3 else cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            mask = np.full(bgr.shape[:2], 255, dtype=np.uint8)
        return bgr, mask

    def _l2_normalize(self, v: list[float] | np.ndarray) -> list[float]:
        arr = np.array(v, dtype=np.float64)
        norm = np.linalg.norm(arr)
        if norm < 1e-10:
            return arr.tolist()
        return (arr / norm).tolist()

    def _largest_contour(self, mask: np.ndarray):
        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        if not contours:
            return None
        return max(contours, key=cv2.contourArea)

    def _crop_to_mask(
        self, bgr: np.ndarray, mask: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """Crop ảnh + mask về bounding box của vùng quả để loại bớt padding nền."""
        coords = cv2.findNonZero(mask)
        if coords is None:
            return bgr, mask
        x, y, w, h = cv2.boundingRect(coords)
        return bgr[y : y + h, x : x + w], mask[y : y + h, x : x + w]

    # ---------- Color (HSV histogram) ----------
    def _build_color_vector(self, bgr: np.ndarray, mask: np.ndarray) -> list[float]:
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist(
            [hsv], [0, 1, 2], mask, [16, 8, 8], [0, 180, 0, 256, 0, 256]
        )
        return self._l2_normalize(hist.flatten())

    # ---------- Color moments (mean/std/skew per channel, masked) ----------
    def _build_color_moments_vector(
        self, bgr: np.ndarray, mask: np.ndarray
    ) -> list[float]:
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float64)
        scales = [180.0, 255.0, 255.0]
        sel = mask > 0
        if not np.any(sel):
            return [0.0] * 9

        moments = []
        for i in range(3):
            channel = hsv[:, :, i][sel] / scales[i]
            mean = float(channel.mean())
            std = float(channel.std())
            centered = channel - mean
            skew = float(np.cbrt(np.mean(centered**3)))
            moments.extend([mean, std, skew])
        return self._l2_normalize(moments)

    # ---------- LBP texture (masked histogram) ----------
    def _build_texture_vector(self, bgr: np.ndarray, mask: np.ndarray) -> list[float]:
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        lbp = local_binary_pattern(gray, P=8, R=1, method="uniform")
        sel = mask > 0
        values = lbp[sel] if np.any(sel) else lbp.ravel()
        hist, _ = np.histogram(values, bins=10, range=(0, 10))
        return self._l2_normalize(hist)

    # ---------- Hu moments from binary mask ----------
    def _build_shape_vector(self, bgr: np.ndarray, mask: np.ndarray) -> list[float]:
        moments = cv2.moments(mask, binaryImage=True)
        hu = cv2.HuMoments(moments).flatten()
        hu_log = [
            -1 * math.copysign(1.0, hu[i]) * math.log10(abs(hu[i]) + 1e-11)
            for i in range(7)
        ]
        return self._l2_normalize(hu_log)

    # ---------- GLCM on masked, bbox-cropped gray ----------
    def _build_glcm_vector(self, bgr: np.ndarray, mask: np.ndarray) -> list[float]:
        crop_bgr, crop_mask = self._crop_to_mask(bgr, mask)
        if crop_bgr.size == 0:
            return [0.0, 0.0, 0.0, 0.0]
        gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
        gray = (gray // 4).astype(np.uint8)
        # Đặt nền (alpha=0) về một giá trị "đặc biệt" để tránh đóng góp giả vào GLCM:
        # dùng level 0 cho cả nền và pixel gray=0 thì mất phân biệt; thay vào đó
        # ta xây ma trận chỉ trên các pixel inside mask thông qua việc set background
        # = mode của fruit pixel (giảm artefact biên).
        sel = crop_mask > 0
        if not np.any(sel):
            return [0.0, 0.0, 0.0, 0.0]
        bg_fill = int(np.median(gray[sel]))
        gray = np.where(sel, gray, bg_fill).astype(np.uint8)

        glcm = graycomatrix(
            gray,
            distances=[1],
            angles=[0, np.pi / 4, np.pi / 2],
            levels=64,
            symmetric=True,
            normed=True,
        )
        contrast = float(graycoprops(glcm, "contrast").mean())
        correlation = float(graycoprops(glcm, "correlation").mean())
        energy = float(graycoprops(glcm, "energy").mean())
        homogeneity = float(graycoprops(glcm, "homogeneity").mean())

        return self._l2_normalize([contrast, correlation, energy, homogeneity])

    # ---------- Gabor (masked mean/std per kernel) ----------
    def _build_gabor_vector(self, bgr: np.ndarray, mask: np.ndarray) -> list[float]:
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        sel = mask > 0

        ksize = 21
        sigmas = [3, 5]
        thetas = [0, np.pi / 4, np.pi / 2, 3 * np.pi / 4]
        lambd = 10
        gamma = 0.5

        features = []
        for sigma in sigmas:
            for theta in thetas:
                kernel = cv2.getGaborKernel(
                    (ksize, ksize), sigma, theta, lambd, gamma, 0, ktype=cv2.CV_32F
                )
                filtered = cv2.filter2D(gray, cv2.CV_8UC3, kernel)
                values = filtered[sel] if np.any(sel) else filtered.ravel()
                features.append(float(values.mean()))
                features.append(float(values.std()))

        return self._l2_normalize(features)

    # ---------- HOG on tightly-cropped fruit ----------
    def _build_hog_vector(self, bgr: np.ndarray, mask: np.ndarray) -> list[float]:
        crop_bgr, _ = self._crop_to_mask(bgr, mask)
        if crop_bgr.size == 0:
            crop_bgr = bgr
        gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (128, 128))
        hog_vec = hog(
            resized,
            orientations=9,
            pixels_per_cell=(8, 8),
            cells_per_block=(2, 2),
            block_norm="L2-Hys",
            feature_vector=True,
        )
        return self._l2_normalize(hog_vec)

    # ---------- Convex hull descriptors from mask ----------
    def _build_convex_hull_vector(
        self, bgr: np.ndarray, mask: np.ndarray
    ) -> list[float]:
        cnt = self._largest_contour(mask)
        if cnt is None:
            return [0.0, 0.0, 0.0]

        hull = cv2.convexHull(cnt)
        area = cv2.contourArea(cnt)
        hull_area = cv2.contourArea(hull)
        if hull_area == 0:
            return [0.0, 0.0, 0.0]

        solidity = float(area / hull_area)

        x, y, w, h = cv2.boundingRect(cnt)
        rect_area = w * h
        extent = float(area / rect_area) if rect_area > 0 else 0.0

        perimeter = cv2.arcLength(cnt, True)
        hull_perimeter = cv2.arcLength(hull, True)
        convexity = float(hull_perimeter / perimeter) if perimeter > 0 else 0.0

        return self._l2_normalize([solidity, extent, convexity])

    # ---------- Aspect ratio of mask bbox ----------
    def _build_aspect_ratio_vector(
        self, bgr: np.ndarray, mask: np.ndarray
    ) -> list[float]:
        cnt = self._largest_contour(mask)
        if cnt is None:
            return [0.0]
        _, _, w, h = cv2.boundingRect(cnt)
        aspect_ratio = float(w / h) if h > 0 else 0.0
        return self._l2_normalize([aspect_ratio])

    # ---------- Zernike moments from mask ----------
    def _build_zernike_vector(self, bgr: np.ndarray, mask: np.ndarray) -> list[float]:
        resized = cv2.resize(mask, (128, 128), interpolation=cv2.INTER_NEAREST)
        radius = 64
        zernike = mahotas.features.zernike_moments(resized, radius)
        return self._l2_normalize(zernike)
