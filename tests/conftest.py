"""Pytest configuration and fixtures."""

import sys
from unittest.mock import MagicMock

import pytest


def pytest_configure(config):
    """Configure pytest environment."""
    # 1. Mock qwen-tts before any imports
    qwen_tts_mock = MagicMock()

    # Mock Qwen3TTSModel class
    class MockQwen3TTSModel:
        @classmethod
        def from_pretrained(cls, *args, **kwargs):
            mock_model = MagicMock()
            import numpy as np

            # Mock generate methods to return (list of numpy arrays, sample_rate)
            mock_audio = np.zeros(24000, dtype=np.float32)
            mock_model.generate_voice_clone.return_value = ([mock_audio], 24000)
            mock_model.generate_voice_design.return_value = ([mock_audio], 24000)
            mock_model.generate_custom_voice.return_value = ([mock_audio], 24000)
            return mock_model

    qwen_tts_mock.Qwen3TTSModel = MockQwen3TTSModel

    # Apply the mock to sys.modules
    sys.modules["qwen_tts"] = qwen_tts_mock


@pytest.fixture(autouse=True)
def mock_system_dependencies(monkeypatch):
    """Mock system checks for all tests."""
    import subprocess

    # Import torch if available, otherwise create a lightweight stub so tests
    # can run without the actual torch dependency.
    import importlib

    try:
        torch = importlib.import_module("torch")
        sys.modules["torch"] = torch
    except ImportError:
        # Use our local shim if available (for lightweight test envs)
        try:
            # Prefer a local shim if present (torch.py in repo root)
            torch = importlib.import_module("torch")
            sys.modules["torch"] = torch
        except ImportError:
            import types

            torch = types.ModuleType("torch")

            class _CudaStub:
                @staticmethod
                def is_available() -> bool:
                    return True

                @staticmethod
                def get_device_name(_):
                    return "Mock NVIDIA GPU"

            setattr(torch, "cuda", _CudaStub())
            # register shim
            sys.modules["torch"] = torch

    # 1. Mock torch.cuda.is_available to return True
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "get_device_name", lambda x: "Mock NVIDIA GPU")

    # 2. Mock subprocess.run for sox check
    original_run = subprocess.run

    def side_effect(*args, **kwargs):
        cmd = args[0] if args else kwargs.get("args", [])
        if cmd and cmd[0] == "sox" and "--version" in cmd:
            mock_ret = MagicMock()
            mock_ret.stdout = "sox:      SoX v14.4.2"
            mock_ret.returncode = 0
            return mock_ret
        return original_run(*args, **kwargs)

    monkeypatch.setattr(subprocess, "run", side_effect)
