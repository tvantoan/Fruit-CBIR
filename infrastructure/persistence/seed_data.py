import os
import traceback
import cv2
import argparse
from psycopg2.extras import RealDictCursor
from infrastructure.database.database import Database
from domain.usecase import IFeatureExtractor

class SeedData:
    def __init__(self, feature_extractor: IFeatureExtractor):
        self.feature_extractor = feature_extractor

    def execute(self):
        parser = argparse.ArgumentParser(description="Hãy chọn hành động:")
        parser.add_argument(
        'mode',
        choices=['clear', 'reset', 'skip'],
        help="Chọn chế độ: clear (xóa sạch), reset (xóa & seed mới), skip (không làm gì)"
    )

        args = parser.parse_args()

        if args.mode == 'clear':
            print("Đang xóa toàn bộ dữ liệu trong bảng images và features...")
            self.clear_all_data()
            print("Đã dọn dẹp sạch sẽ!")
            self.seed_data()
            print("Đã Seed lại dữ liệu thành công!")

        elif args.mode == 'reset':
            print("Bắt đầu reset: Xóa dữ liệu cũ và thực hiện Seed mới...")
            self.clear_all_data()
            self.seed_data()
            print("Đã Reset và Seed thành công!")

        else:
            print("Bỏ qua công đoạn seed data. Khởi động App...")
            pass

    def clear_all_data(self):
        conn = Database.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("TRUNCATE TABLE features, images, fruits RESTART IDENTITY CASCADE;")
                conn.commit()
        finally:
            Database.return_connection(conn)

    def seed_data(self):
        conn = Database.get_connection()
        try:

            with conn.cursor() as cur:
                base_dir = os.path.dirname(__file__)
                dataset_path = os.path.abspath(os.path.join(base_dir, '..', '..', 'static', 'Fruits_data_processed'))

                if not os.path.exists(dataset_path):
                    print(f"Error: Dataset path not found at {dataset_path}")
                    return

                for category_dir in sorted(os.listdir(dataset_path)):
                    category_path = os.path.join(dataset_path, category_dir)
                    if not os.path.isdir(category_path):
                        continue


                    fruit_name = category_dir.replace('_processed', '')
                    print(f"Seeding category: {fruit_name}...")

                    cur.execute("INSERT INTO fruits (name) VALUES (%s) RETURNING fruit_id", (fruit_name,))
                    fruit_id = cur.fetchone()[0]

                    for filename in sorted(os.listdir(category_path)):
                        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                            continue

                        relative_path = os.path.join(category_dir, filename)

                        cur.execute(
                            "INSERT INTO images (filename, filepath, fruit_id) VALUES (%s, %s, %s) RETURNING image_id",
                            (filename, relative_path, fruit_id)
                        )
                        image_id = cur.fetchone()[0]


                        full_image_path = os.path.join(category_path, filename)

                        image_ndarray = cv2.imread(full_image_path)

                        if image_ndarray is not None:
                            extracted_features = self.feature_extractor.execute(image_ndarray)
                        else:
                            print(f"Lỗi: Không thể đọc ảnh tại {full_image_path}")
                            continue
                        cur.execute(
                            """INSERT INTO features (image_id, color, texture, shape)
                               VALUES (%s, %s::vector, %s::vector, %s::vector)""",
                            (
                                image_id,
                                extracted_features['color'],
                                extracted_features['texture'],
                                extracted_features['shape'],
                            )
                        )

            conn.commit()
            print("Seeding completed successfully!")

        except Exception as e:
            conn.rollback()
            print("--- SEEDING ERROR ---")
            traceback.print_exc()
        finally:
            Database.return_connection(conn)