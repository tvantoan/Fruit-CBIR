CREATE TABLE IF NOT EXISTS images (
    image_id    SERIAL PRIMARY KEY,
    filename    VARCHAR(255) NOT NULL,
    filepath    TEXT NOT NULL,
    fruit_label VARCHAR(100) NOT NULL,
    width       INTEGER,
    height      INTEGER,
    file_size_kb REAL,
    date_added  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS features (
    feature_id     SERIAL PRIMARY KEY,
    image_id       INTEGER NOT NULL REFERENCES images(image_id) ON DELETE CASCADE,
    feature_type   VARCHAR(50) NOT NULL,
    feature_vector BYTEA NOT NULL,
    vector_dim     INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS query_logs (
    query_id      SERIAL PRIMARY KEY,
    query_image   TEXT NOT NULL,
    result_ids    TEXT NOT NULL,
    distances     TEXT NOT NULL,
    query_time_ms REAL,
    query_date    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_images_label ON images(fruit_label);
CREATE INDEX IF NOT EXISTS idx_features_type ON features(feature_type);
CREATE INDEX IF NOT EXISTS idx_features_image ON features(image_id);
