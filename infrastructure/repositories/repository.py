"""PostgreSQL database implementation of repositories."""

import json
import os

from pgvector import Vector
import psycopg2
from psycopg2.extras import RealDictCursor

from domain.constants import LIMIT_SAMPLE_IMAGES_PER_FRUIT, LIMIT_SIMILAR_IMAGES
from domain.models import Feature, Image, Fruit
from domain.repositories import IFeatureRepository, IImageRepository, IFruitRepository
from infrastructure.database.database import Database

class FruitRepository(IFruitRepository):
    """PostgreSQL implementation of FruitRepository."""
    def create(self, name: str) -> int:
        """Create and persist fruit, return fruit_id."""
        conn = Database.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO fruits (name) VALUES (%s) RETURNING fruit_id",
                    (name,)
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
                    (filename, filepath, fruit_id)
                )
                row = cur.fetchone()
                if not row or 'image_id' not in row:
                    raise RuntimeError('Failed to insert image')

                image_id = row['image_id']
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
                    (fruit_id, LIMIT_SAMPLE_IMAGES_PER_FRUIT)
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

    def create(self, image_id: int, color:  list[float], texture:  list[float], shape:  list[float]) -> int:
        """Store feature vector."""
        conn = Database.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO features (image_id, color, texture, shape)
                    VALUES (%s, %s::vector, %s::vector, %s::vector)
                    RETURNING feature_id
                    """,
                    (image_id, color, texture, shape)
                )
                feature_id = cur.fetchone()['feature_id']
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
                cur.execute(
                    "SELECT feature_id, image_id, color, texture, shape FROM features WHERE image_id = %s",
                    (image_id,)
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

    def search_similar(self, features: dict, weights: dict[str, float]) -> list[dict]:
        conn = Database.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:

                sql = """
                    SELECT
                        i.filename, i.filepath, fr.name AS fruit_name,
                        (f.color <=> %(v_c)s::vector) AS dist_c,
                        (f.texture <=> %(v_t)s::vector) AS dist_t,
                        (f.shape <=> %(v_s)s::vector) AS dist_s,
                        (
                            %(w_c)s * (f.color <=> %(v_c)s::vector) +
                            %(w_t)s * (f.texture <=> %(v_t)s::vector) +
                            %(w_s)s * (f.shape <=> %(v_s)s::vector)
                        ) AS weighted_distance
                    FROM features f
                    JOIN images i ON f.image_id = i.image_id
                    JOIN fruits fr ON i.fruit_id = fr.fruit_id
                    ORDER BY weighted_distance ASC
                    LIMIT %(limit)s;
                """

                params = {
                    'w_c': weights.get('color', 0.33),
                    'v_c': features['color'],
                    'w_t': weights.get('texture', 0.33),
                    'v_v': features['texture'],
                    'v_t': features['texture'],
                    'w_s': weights.get('shape', 0.33),
                    'v_s': features['shape'],
                    'limit': LIMIT_SIMILAR_IMAGES
                }

                cur.execute(sql, params)
                results = cur.fetchall()


                for r in results:
                    r['distance'] = float(r['weighted_distance'])
                    r['similarity'] = round(1 - r['distance'], 4)
                    r['feature_distances'] = {
                        'color': round(float(r['dist_c']) * params['w_c'], 4),
                        'texture': round(float(r['dist_t']) * params['w_t'], 4),
                        'shape': round(float(r['dist_s']) * params['w_s'], 4)
                    }
                return results
        finally:
            Database.return_connection(conn)

    def _row_to_feature(self, row: dict):
        return Feature(
            feature_id=row['feature_id'],
            image_id=row['image_id'],
            color=row['color'],
            texture=row['texture'],
            shape=row['shape'],
        )
