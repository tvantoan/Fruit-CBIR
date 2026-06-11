"""PostgreSQL database implementation of repositories."""

import json
import os

from pgvector import Vector
import psycopg2
from psycopg2.extras import RealDictCursor

from domain.constants import (
    FEATURE_KEYS,
    LIMIT_SAMPLE_IMAGES_PER_FRUIT,
    LIMIT_SIMILAR_IMAGES,
)
from domain.models import Feature, Image, Fruit
from domain.repositories import IFeatureRepository, IImageRepository, IFruitRepository
from infrastructure.database.database import Database
from infrastructure.helper import normalize_weights


class FruitRepository(IFruitRepository):
    """PostgreSQL implementation of FruitRepository."""

    def create(self, name: str) -> int:
        """Create and persist fruit, return fruit_id."""
        conn = Database.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO fruits (name) VALUES (%s) RETURNING fruit_id", (name,)
                )
                fruit_id = cur.fetchone()[0]
            conn.commit()
            return fruit_id
        except Exception as e:
            conn.rollback()
            print(f"Error creating fruit: {e}")
            raise e
        finally:
            Database.return_connection(conn)

    def get_id_by_name(self, name: str) -> int:
        """Get fruit_id by name."""
        conn = Database.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT fruit_id FROM fruits WHERE name = %s", (name,))
                row = cur.fetchone()
                return row[0]
        finally:
            Database.return_connection(conn)

    def get_all(self) -> list[Fruit]:
        """Get all fruits."""
        conn = Database.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT fruit_id, name FROM fruits")
                return [self._row_to_fruit(row) for row in cur.fetchall()]
        finally:
            Database.return_connection(conn)

    def _row_to_fruit(self, row: dict) -> Fruit:
        """Chuyển đổi Dict từ DB sang Dataclass Fruit."""
        return Fruit(**row)


class ImageRepository(IImageRepository):
    """PostgreSQL implementation of ImageRepository."""

    def create(self, filename: str, filepath: str, fruit_id: int) -> int:
        """Create and persist image, return image_id."""
        conn = Database.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """INSERT INTO images (filename, filepath, fruit_id)
                       VALUES (%s, %s, %s) RETURNING image_id""",
                    (filename, filepath, fruit_id),
                )
                row = cur.fetchone()
                if not row or "image_id" not in row:
                    raise RuntimeError("Failed to insert image")

                image_id = row["image_id"]
            conn.commit()
            return image_id

        except Exception as e:
            conn.rollback()
            print(f"Error creating image: {e}")
            raise e
        finally:
            Database.return_connection(conn)

    def get_by_id(self, image_id: int) -> Image | None:
        """Retrieve image by ID."""
        conn = Database.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM images WHERE image_id = %s", (image_id,))
                row = cur.fetchone()
                if row is None:
                    return None
                return self._row_to_image(row)
        finally:
            Database.return_connection(conn)

    def get_sample_by_fruit_id(self, fruit_id: int) -> Image | None:
        """Get sample images for a fruit."""
        conn = Database.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM images WHERE fruit_id = %s LIMIT %s",
                    (fruit_id, LIMIT_SAMPLE_IMAGES_PER_FRUIT),
                )
                row = cur.fetchone()
                if row is None:
                    return None
                return self._row_to_image(row)
        finally:
            Database.return_connection(conn)

    def _row_to_image(self, row: dict) -> Image:
        """Chuyển đổi Dict từ DB sang Dataclass Image."""
        return Image(**row)


class FeatureRepository(IFeatureRepository):
    """PostgreSQL implementation of FeatureRepository."""

    def create(self, image_id: int, features: dict[str, list[float]]) -> int:
        """Store feature vectors for all FEATURE_KEYS."""
        missing_keys = [key for key in FEATURE_KEYS if key not in features]
        if missing_keys:
            raise ValueError(f"Missing required feature keys: {missing_keys}")

        conn = Database.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                feature_columns = ", ".join(FEATURE_KEYS)
                placeholders = ", ".join(["%s::vector" for _ in FEATURE_KEYS])
                values = [image_id] + [features[key] for key in FEATURE_KEYS]

                cur.execute(
                    f"""
                    INSERT INTO features (image_id, {feature_columns})
                    VALUES (%s, {placeholders})
                    RETURNING feature_id
                    """,
                    tuple(values),
                )
                feature_id = cur.fetchone()["feature_id"]
            conn.commit()
            return feature_id
        except Exception as e:
            conn.rollback()
            print(f"Error creating feature: {e}")
            raise e
        finally:
            Database.return_connection(conn)

    def get_by_image_id(self, image_id: int) -> Feature | None:
        """Retrieve all features for image."""
        conn = Database.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                selected_columns = ", ".join(["feature_id", "image_id"] + FEATURE_KEYS)
                cur.execute(
                    f"SELECT {selected_columns} FROM features WHERE image_id = %s",
                    (image_id,),
                )
                rows = cur.fetchone()
                return self._row_to_feature(rows) if rows else None
        finally:
            Database.return_connection(conn)

    def delete_by_image_id(self, image_id: int) -> None:
        """Delete all features for image."""
        conn = Database.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM features WHERE image_id = %s", (image_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error deleting feature by image_id={image_id}: {e}")
            raise e
        finally:
            Database.return_connection(conn)

    def search_similar(
        self,
        features: dict,
        weights: dict[str, float],
        limit: int | None = None,
    ) -> list[dict]:
        """Weighted cosine search across feature vectors with normalized weights."""
        conn = Database.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                normalized_weights = normalize_weights(weights)

                # SỬA TẠI ĐÂY: Dùng {{ }} để thoát dấu ngoặc nhọn trong f-string
                # Hoặc dùng định dạng %s truyền thống của psycopg2
                dist_selects = [
                    f"COALESCE(f.{key} <=> %(v_{key})s::vector, 1.0) AS dist_{key}"
                    for key in FEATURE_KEYS
                ]
                weighted_terms = [
                    f"%(w_{key})s * COALESCE(f.{key} <=> %(v_{key})s::vector, 1.0)"
                    for key in FEATURE_KEYS
                ]

                sql = f"""
                    SELECT
                        i.filename, i.filepath, fr.name AS fruit_name,
                        {',\n                    '.join(dist_selects)},
                        (
                            { ' + '.join(weighted_terms) }
                        ) AS weighted_distance
                    FROM features f
                    JOIN images i ON f.image_id = i.image_id
                    JOIN fruits fr ON i.fruit_id = fr.fruit_id
                    ORDER BY weighted_distance ASC
                    LIMIT %(limit)s;
                """

                # Xây dựng params khớp chính xác với key trong SQL
                params = {}
                for key in FEATURE_KEYS:
                    params[f"w_{key}"] = normalized_weights.get(key, 0)
                    params[f"v_{key}"] = features.get(key, [])  # Dùng .get để an toàn

                params["limit"] = limit if limit is not None else LIMIT_SIMILAR_IMAGES

                cur.execute(sql, params)
                results = cur.fetchall()

                for r in results:
                    r["distance"] = float(r["weighted_distance"])
                    r["similarity"] = round(1 - r["distance"], 4)
                    r["feature_distances"] = {
                        key: round(
                            float(r[f"dist_{key}"]) * normalized_weights.get(key, 0), 4
                        )
                        for key in FEATURE_KEYS
                    }
                return results
        finally:
            Database.return_connection(conn)

    def count_per_fruit(self) -> dict[str, int]:
        """Return number of indexed images per fruit name."""
        conn = Database.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT fr.name, COUNT(f.feature_id) AS cnt
                    FROM features f
                    JOIN images i ON f.image_id = i.image_id
                    JOIN fruits fr ON i.fruit_id = fr.fruit_id
                    GROUP BY fr.name
                    """
                )
                return {name: int(cnt) for name, cnt in cur.fetchall()}
        finally:
            Database.return_connection(conn)

    def _row_to_feature(self, row: dict):
        # Lọc lấy những dữ liệu có trong row mà Feature cần
        return Feature(**{k: row[k] for k in Feature.__annotations__.keys()})
