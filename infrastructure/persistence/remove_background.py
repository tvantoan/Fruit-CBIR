import os
import numpy as np
from rembg import remove
import cv2


def preprocess_image_for_rembg(image: np.ndarray, target_size: int = 224) -> np.ndarray:
    """
    Quy trình nhất quán: Tách nền -> Crop sát -> Resize & Pad (4 kênh)
    """

    # 1. Tách nền (vẫn giữ nguyên 4 kênh RGBA)
    res_rgba = remove(image)
    alpha = res_rgba[:, :, 3]

    # 2. Tìm vùng chứa đối tượng (Kết hợp alpha > 0 và boundingRect)
    coords = cv2.findNonZero(alpha)

    if coords is None:
        # Nếu không tìm thấy đối tượng, trả về khung trống trong suốt
        return np.zeros((target_size, target_size, 4), dtype=np.uint8)

    # Lấy bounding box sát nhất
    x, y, w, h = cv2.boundingRect(coords)
    fruit_crop = res_rgba[y : y + h, x : x + w]

    # 3. Tính toán tỷ lệ và Resize MỘT LẦN duy nhất
    scale = target_size / max(h, w)
    new_w, new_h = int(w * scale), int(h * scale)

    fruit_resized = cv2.resize(
        fruit_crop, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4
    )

    # 4. Tạo canvas 4 kênh (Trong suốt hoàn toàn)
    final_canvas = np.zeros((target_size, target_size, 4), dtype=np.uint8)

    # Đưa ảnh vào chính giữa
    off_x = (target_size - new_w) // 2
    off_y = (target_size - new_h) // 2
    final_canvas[off_y : off_y + new_h, off_x : off_x + new_w] = fruit_resized

    return final_canvas


if __name__ == "__main__":
    fruits = [
        "Strawberries",
    ]
    for fruit in fruits:
        input_path = f"/home/kiiri/projects/fruit/static/Fruits_data/{fruit}"
        output_path = (
            f"/home/kiiri/projects/fruit/static/Fruits_data_processed/{fruit}_processed"
        )
        os.makedirs(output_path, exist_ok=True)

        for file_name in os.listdir(input_path):
            img_name = file_name.split(".")[0]
            img_path = os.path.join(input_path, file_name)
            image = cv2.imread(img_path)

            if image is not None:
                processed_image = preprocess_image_for_rembg(image)
                save_path = os.path.join(output_path, f"{img_name}.png")
                cv2.imwrite(save_path, processed_image)
                print(f"Processed and saved: {save_path}")
            else:
                print(f"Failed to read image: {img_path}")
