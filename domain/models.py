"""Domain entities and value objects."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from pgvector import Vector

@dataclass
class Fruit:
    fruit_id: int
    name: str
    description: Optional[str] = None

@dataclass
class Image:
    """Image entity - represents an uploaded/indexed fruit image."""
    image_id: int
    fruit_id: int
    filename: str
    filepath: str

@dataclass
class Feature:
    """Feature vector entity - extracted features from an image."""
    feature_id: int
    image_id: int
    color: list[float]
    color_moments: list[float]
    texture: list[float]
    glcm: list[float]
    shape: list[float]
