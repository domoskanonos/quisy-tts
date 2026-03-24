"""Lightweight torch shim for environments without PyTorch installed.

This shim is only used in development/test environments where the real
`torch` package is not available. It provides a minimal subset of the
interface used by the project tests so imports succeed.

Do not rely on this for production inference.
"""

from __future__ import annotations

import numpy as np
from types import SimpleNamespace
from typing import Any


class _CudaStub:
    @staticmethod
    def is_available() -> bool:
        return False

    @staticmethod
    def get_device_name(idx: int = 0) -> str:
        return "Mock GPU"


cuda = _CudaStub()

# Minimal dtype placeholders
float32 = np.float32
try:
    bfloat16 = np.dtype("bfloat16")
except Exception:
    # Fallback: use float32 when bfloat16 isn't supported in this environment
    bfloat16 = np.float32


def zeros(*shape: int, dtype: Any = None):
    dt = np.float32 if dtype is None else (dtype if isinstance(dtype, type) else np.float32)
    return np.zeros(shape, dtype=dt)


def from_numpy(arr: np.ndarray):
    return arr


# Provide a simple Tensor-like wrapper when necessary
class Tensor(np.ndarray):
    @staticmethod
    def _make(x: np.ndarray):
        return x.view(Tensor)

    def cpu(self):
        return self

    def float(self):
        return self

    def unsqueeze(self, dim: int):
        return np.expand_dims(self, axis=dim)


def from_numpy_tensor(arr: np.ndarray):
    return Tensor._make(arr)


__all__ = ["cuda", "zeros", "from_numpy", "from_numpy_tensor", "float32", "bfloat16"]
