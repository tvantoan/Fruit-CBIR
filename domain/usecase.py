from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Any
from PIL import Image, ImageFilter, ImageOps, ImageStat

from domain.dtos import SearchResult
import numpy as np

T = TypeVar('T')
class IUseCase(ABC, Generic[T]):
    """Base interface for all use cases."""
    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> T:
        """Execute the use case with given arguments."""
        pass

class IFeatureExtractor(IUseCase[dict[str, list[float]]]):
    """Abstract feature extractor - defines interface for extracting features from images."""

    @abstractmethod
    def execute(self, image_data: np.ndarray) -> dict[str, list[float]]:
        """Extract features from image at given filepath and return as dict."""
        pass
    @abstractmethod
    def _build_color_vector(self, image: np.ndarray) -> list[float]:
        """Extract color features and return as vector."""
        pass
    @abstractmethod
    def _build_texture_vector(self, image: np.ndarray) -> list[float]:
        """Extract texture features and return as vector."""
        pass
    @abstractmethod
    def _build_shape_vector(self, image: np.ndarray) -> list[float]:
        """Extract shape features and return as vector."""
        pass


class ISearchImage(IUseCase[list[SearchResult]]):
    """Abstract search use case - defines interface for searching similar images."""

    @abstractmethod
    def execute(self, image_data: np.ndarray, weights: dict[str, float]) -> list[SearchResult]:
        """Search for similar images given a query image data and return results."""
        pass

class IRemoveBackground(IUseCase[np.ndarray]):
    """Abstract background remover - defines interface for removing background from images."""

    @abstractmethod
    def execute(self, image_data: np.ndarray) -> np.ndarray:
        """Remove background from image at given path and return processed image."""
        pass
