import os
import numpy as np
from rembg import remove
import cv2

def process(input_dir, output_dir, target_size=224):
    os.makedirs(output_dir, exist_ok=True)
    for filename in os.listdir(input_dir):
        img_path = os.path.join(input_dir, filename)
        img = cv2.imread(img_path)
        if img is None: continue
        ratio = 256 / max(img.shape[:2])
        img = cv2.resize(img, (int(img.shape[1] * ratio), int(img.shape[0] * ratio)), interpolation=cv2.INTER_AREA)

  
        res_rgba = remove(img)
        

        alpha = res_rgba[:, :, 3]
        y, x = np.where(alpha > 0)
        if len(x) == 0: continue
        fruit_crop = res_rgba[y.min():y.max()+1, x.min():x.max()+1]


        h, w = fruit_crop.shape[:2]
        scale = target_size / max(h, w)
        new_w, new_h = int(w * scale), int(h * scale)
        fruit_resized = cv2.resize(fruit_crop, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

        canvas = np.zeros((target_size, target_size, 4), dtype=np.uint8)

        off_x = (target_size - new_w) // 2
        off_y = (target_size - new_h) // 2
        
        canvas[off_y:off_y+new_h, off_x:off_x+new_w] = fruit_resized


        base_name = os.path.splitext(filename)[0]
        save_path = os.path.join(output_dir, f"{base_name}.png")
        cv2.imwrite(save_path, canvas)
        print(f"Đã lưu ảnh trong suốt: {save_path}")
if __name__ == "__main__":
    fruits = [ "Mangoes", "Peaches"]
    for fruit in fruits:
        input_dir = fruit
        output_dir = f"{fruit}_processed"
        process(input_dir, output_dir)