import psycopg2
import psycopg2.pool
import os

from dotenv import load_dotenv

load_dotenv()
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')

class Database:
    _pool = None

    @classmethod
    def initialize(cls):
        if cls._pool is None:
            cls._pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=20,
                dsn=f"dbname={db_name} user={db_user} password={db_password} host={db_host} port={db_port}"
            )
            print("Database pool initialized.")

    @classmethod
    def get_connection(cls):
        if cls._pool is None:
            raise RuntimeError("Database not initialized. Call Database.initialize() first.")
        return cls._pool.getconn()

    @classmethod
    def return_connection(cls, connection):
        if cls._pool is None:
            raise RuntimeError("Database not initialized. Call Database.initialize() first.")
        cls._pool.putconn(connection)

    @classmethod
    def close_all_connections(cls):
        if cls._pool is None:
            raise RuntimeError("Database not initialized. Call Database.initialize() first.")
        cls._pool.closeall()