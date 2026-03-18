import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://cbir_user:cbir_pass@localhost:5432/fruit_cbir')


def get_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema_path, 'r') as f:
        sql = f.read()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
    finally:
        conn.close()


def insert_image(filename, filepath, fruit_label, width, height, file_size_kb):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO images (filename, filepath, fruit_label, width, height, file_size_kb)
                   VALUES (%s, %s, %s, %s, %s, %s) RETURNING image_id""",
                (filename, filepath, fruit_label, width, height, file_size_kb)
            )
            image_id = cur.fetchone()['image_id']
        conn.commit()
        return image_id
    finally:
        conn.close()


def get_image(image_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM images WHERE image_id = %s", (image_id,))
            return cur.fetchone()
    finally:
        conn.close()


def get_all_images(limit=100, offset=0):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM images ORDER BY image_id LIMIT %s OFFSET %s", (limit, offset))
            return cur.fetchall()
    finally:
        conn.close()


def get_images_by_label(fruit_label):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM images WHERE fruit_label = %s", (fruit_label,))
            return cur.fetchall()
    finally:
        conn.close()


def insert_feature(image_id, feature_type, feature_vector_bytes, vector_dim):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO features (image_id, feature_type, feature_vector, vector_dim)
                   VALUES (%s, %s, %s, %s) RETURNING feature_id""",
                (image_id, feature_type, psycopg2.Binary(feature_vector_bytes), vector_dim)
            )
            feature_id = cur.fetchone()['feature_id']
        conn.commit()
        return feature_id
    finally:
        conn.close()


def get_features(image_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT feature_id, feature_type, vector_dim FROM features WHERE image_id = %s", (image_id,))
            return cur.fetchall()
    finally:
        conn.close()


def log_query(query_image, result_ids, distances, query_time_ms):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO query_logs (query_image, result_ids, distances, query_time_ms)
                   VALUES (%s, %s, %s, %s)""",
                (query_image, json.dumps(result_ids), json.dumps(distances), query_time_ms)
            )
        conn.commit()
    finally:
        conn.close()


def get_stats():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as total FROM images")
            total_images = cur.fetchone()['total']

            cur.execute("SELECT fruit_label, COUNT(*) as count FROM images GROUP BY fruit_label ORDER BY fruit_label")
            categories = cur.fetchall()

            cur.execute("SELECT COUNT(*) as total FROM features")
            total_features = cur.fetchone()['total']

            cur.execute("SELECT COUNT(*) as total FROM query_logs")
            total_queries = cur.fetchone()['total']

            return {
                'total_images': total_images,
                'categories': categories,
                'total_features': total_features,
                'total_queries': total_queries,
            }
    finally:
        conn.close()


def get_random_images(n=5):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM images ORDER BY RANDOM() LIMIT %s", (n,))
            return cur.fetchall()
    finally:
        conn.close()
