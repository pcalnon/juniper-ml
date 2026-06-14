"""The model-serialization strategy interface.

A standalone strategy (decision D6) -- not a model method -- so the persistence *format* is
decoupled from the model. cascor's HDF5 serializer and the LMU's hyperparameter +
eigendecomposition serializer each become one implementation. The conformance kit asserts a
``save`` -> ``load`` round-trip is *lossless*: predictions are identical after reload.

Per RK-8 this lives in juniper-model-core; a dedicated serialization package is resisted
until a third independent format actually exists.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import os

    from juniper_model_core.interfaces import TrainableModel

__all__ = ["ModelSerializer"]


class ModelSerializer(ABC):
    """Persist and restore a :class:`TrainableModel`."""

    @abstractmethod
    def save(self, model: TrainableModel, path: str | os.PathLike[str]) -> None:
        """Write ``model`` to ``path``."""

    @abstractmethod
    def load(self, path: str | os.PathLike[str]) -> TrainableModel:
        """Reconstruct a model previously written by :meth:`save`."""
