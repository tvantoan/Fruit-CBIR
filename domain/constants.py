SERVED_IMAGE_API = "/api/static/images/"
SERVED_IMAGE_ROUTE = "/static/images/"
LIMIT_SIMILAR_IMAGES = 5
LIMIT_SAMPLE_IMAGES_PER_FRUIT = 1
DATA_PATH = "static/Fruits_data_processed/"
TRAIN_DATA_PATH = "static/Fruits_data_train/"
TEST_DATA_PATH = "static/Fruits_data_test/"

FEATURE_KEYS = [
    "color",
    "color_moments",
    "texture",
    "glcm",
    "shape",
    "gabor",
    "hog",
    "convex_hull",
    "aspect_ratio",
    "zernike",
]

FEATURE_DIMENSIONS = {
    "color": 1024,
    "color_moments": 9,
    "texture": 10,
    "glcm": 4,
    "shape": 7,
    "gabor": 16,
    "hog": 8100,
    "convex_hull": 3,
    "aspect_ratio": 1,
    "zernike": 25,
}
