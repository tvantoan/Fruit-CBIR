from domain.constants import SERVED_IMAGE_API
from domain.repositories import IFeatureRepository, IImageRepository, IFruitRepository
from domain.usecase import IFeatureExtractor, ISearchImage, IRemoveBackground
from domain.dtos import SearchResult
import numpy as np

class SearchImagesUseCase(ISearchImage):
    def __init__(self, image_repo: IImageRepository, feature_repo: IFeatureRepository,
                 feature_extractor: IFeatureExtractor, fruit_repo: IFruitRepository, background_remover: IRemoveBackground):
        self.image_repo = image_repo
        self.feature_repo = feature_repo
        self.feature_extractor = feature_extractor
        self.fruit_repo = fruit_repo
        self.background_remover = background_remover

    def execute(self, image_data: np.ndarray, weights: dict[str, float]) -> list[SearchResult]:

        extracted_features = self.feature_extractor.execute(image_data)
        required = ('color', 'color_moments', 'texture', 'glcm', 'shape')
        if not extracted_features or any(not extracted_features.get(k) for k in required):
            return []

        similar_images = self.feature_repo.search_similar(
            {k: extracted_features[k] for k in required},
            weights,
        )
        results = []
        for row in similar_images:
            results.append(SearchResult(
                image_url=f"{SERVED_IMAGE_API}{row['filepath']}",
                fruit_name=row['fruit_name'],
                similarity=round(row['similarity'], 4),
                distance=round(row['distance'], 4),
                feature_distances=row['feature_distances']
            ))

        return results