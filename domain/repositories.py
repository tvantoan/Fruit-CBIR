"""Domain repository interfaces (abstract contracts)."""

from abc import ABC, abstractmethod

from domain.models import Image, Feature, Fruit


class IFruitRepository(ABC):
    """Abstract repository for fruit persistence."""

    @abstractmethod
    def create(self, name: str) -> int:
        """Create fruit and return fruit_id."""
        pass

    @abstractmethod
    def get_id_by_name(self, name: str) -> int:
        """Get fruit_id by name."""
        pass

    @abstractmethod
    def get_all(self) -> list[Fruit]:
        """Get all fruits."""
        pass


class IImageRepository(ABC):
    """Abstract repository for image persistence."""

    @abstractmethod
    def create(self, filename: str, filepath: str, fruit_id: int) -> int:
        """Create image and return image_id."""
        pass

    @abstractmethod
    def get_by_id(self, image_id: int) -> Image | None:
        """Get image by ID."""
        pass

    @abstractmethod
    def get_sample_by_fruit_id(self, fruit_id: int) -> Image | None:
        """Get sample images for a fruit."""
        pass


class IFeatureRepository(ABC):
    """Abstract repository for feature persistence."""

    @abstractmethod
    def create(self, image_id: int, features: dict[str, list[float]]) -> int:
        """Store feature vectors, return feature_id."""
        pass

    @abstractmethod
    def get_by_image_id(self, image_id: int) -> Feature | None:
        """Get all features for an image."""
        pass

    @abstractmethod
    def delete_by_image_id(self, image_id: int) -> None:
        """Delete all features for an image."""
        pass

    @abstractmethod
    def search_similar(
        self, features: dict, weights: dict[str, float], limit: int | None = None
    ) -> list[dict]:
        """Search for similar images based on query vector, return list of dicts with image info and similarity."""
        pass

    @abstractmethod
    def count_per_fruit(self) -> dict[str, int]:
        """Return number of indexed images per fruit name."""
        pass
