import os
import traceback
import cv2
import argparse
from infrastructure.database.database import Database
from domain.usecase import IFeatureExtractor
from domain.constants import FEATURE_KEYS


class SeedData:
    def __init__(self, feature_extractor: IFeatureExtractor):
        self.feature_extractor = feature_extractor

    def execute(self):
        parser = argparse.ArgumentParser(description="Seed Data Configuration")
        parser.add_argument(
            "mode",
            choices=["clear", "reset", "skip"],
            help="clear: xóa sạch, reset: xóa & seed mới, skip: bỏ qua",
        )
        parser.add_argument(
            "--dataset-root",
            type=str,
            default=None,
            help="Đường dẫn đến Fruits_data_train",
        )

        args = parser.parse_args()

        # Xác định đường dẫn tuyệt đối đến thư mục train
        if args.dataset_root:
            self.dataset_root = args.dataset_root
        else:
            self.dataset_root = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__), "..", "..", "static", "Fruits_data_train"
                )
            )

        if args.mode == "clear":
            self.clear_all_data()
            print("Successfully cleared all data.")
        elif args.mode == "reset":
            self.clear_all_data()
            self.seed_data()
            print("Reset and Seeding completed successfully!")
        else:
            print("Skipping seeding process...")

    def clear_all_data(self):
        conn = Database.get_connection()
        try:
            with conn.cursor() as cur:
                print("Cleaning tables: fruits, images, features...")
                cur.execute(
                    "TRUNCATE TABLE features, images, fruits RESTART IDENTITY CASCADE;"
                )
                conn.commit()
        finally:
            Database.return_connection(conn)

    def seed_data(self):
        conn = Database.get_connection()
        try:
            if not os.path.exists(self.dataset_root):
                print(f"Error: Dataset path not found at {self.dataset_root}")
                return

            with conn.cursor() as cur:
                categories = sorted(
                    [
                        d
                        for d in os.listdir(self.dataset_root)
                        if os.path.isdir(os.path.join(self.dataset_root, d))
                    ]
                )

                for category_dir in categories:
                    category_path = os.path.join(self.dataset_root, category_dir)
                    fruit_name = category_dir.replace("_processed", "")

                    # 1. Chèn vào bảng fruits
                    cur.execute(
                        "INSERT INTO fruits (name) VALUES (%s) RETURNING fruit_id",
                        (fruit_name,),
                    )
                    fruit_id = cur.fetchone()[0]
                    print(f"--> Seeding {fruit_name} (ID: {fruit_id})")

                    # Duyệt từng file ảnh trong thư mục loại quả
                    for filename in sorted(os.listdir(category_path)):
                        if not filename.lower().endswith((".png", ".jpg", ".jpeg")):
                            continue

                        full_image_path = os.path.join(category_path, filename)
                        relative_path = os.path.join(category_dir, filename)

                        # 2. Chèn vào bảng images
                        cur.execute(
                            "INSERT INTO images (filename, filepath, fruit_id) VALUES (%s, %s, %s) RETURNING image_id",
                            (filename, relative_path, fruit_id),
                        )
                        image_id = cur.fetchone()[0]

                        # 3. Trích xuất đặc trưng
                        image_ndarray = cv2.imread(
                            full_image_path, cv2.IMREAD_UNCHANGED
                        )
                        if image_ndarray is None:
                            print(f"Skip: Could not read {filename}")
                            continue

                        extracted = self.feature_extractor.execute(image_ndarray)

                        # 4. Chuẩn bị SQL động cho bảng features
                        # Tách riêng các trường là vector và các trường là số thực (float)
                        placeholders = []
                        for key in FEATURE_KEYS:
                            # Nếu là aspect_ratio thì không dùng casting ::vector (vì nó là float)
                            if key == "aspect_ratio":
                                placeholders.append("%s")
                            else:
                                placeholders.append("%s::vector")

                        sql = f"""
                            INSERT INTO features (image_id, {', '.join(FEATURE_KEYS)})
                            VALUES (%s, {', '.join(placeholders)})
                        """

                        values = [image_id] + [
                            extracted.get(key) for key in FEATURE_KEYS
                        ]
                        cur.execute(sql, tuple(values))

                    conn.commit()  # Commit sau mỗi thư mục để tránh treo transaction quá lâu
                    print(f"Finished seeding {fruit_name}")

            print("Done! All training data seeded.")

        except Exception as e:
            conn.rollback()
            print("--- SEEDING ERROR ---")
            traceback.print_exc()
        finally:
            Database.return_connection(conn)
