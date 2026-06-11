from dataclasses import dataclass
from PIL import Image as PILImage


@dataclass
class SearchResult:
    """Search result entity - represents a similar image found during search."""

    image_url: str
    fruit_name: str
    similarity: float
    distance: float
    feature_distances: dict[str, float]
