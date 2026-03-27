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

    @pytest.fixture(autouse=True)
    def setup_test_env(tmp_path, monkeypatch):
        """Setup test environment and patch ProjectConfig settings."""
        # Reset configuration to ensure we don't use stale settings from previous
        # tests or module-level initialization.
        from config import ProjectConfig

        ProjectConfig.reset()

        # Define paths
        models_dir = tmp_path / "models"
        voices_dir = tmp_path / "voices"
        output_dir = tmp_path / "output"
        app_dir = tmp_path / "app_data"
        resources_dir = tmp_path / "resources"

        # Create directories
        for p in [models_dir, voices_dir, output_dir, app_dir, resources_dir]:
            p.mkdir(parents=True, exist_ok=True)

        # Set environment variables
        monkeypatch.setenv("MODELS_DIR", str(models_dir))
        monkeypatch.setenv("VOICES_DIR", str(voices_dir))
        monkeypatch.setenv("OUTPUT_DIR", str(output_dir))
        monkeypatch.setenv("APP_DIR", str(app_dir))
        monkeypatch.setenv("RESOURCES_DIR", str(resources_dir))
        monkeypatch.setenv(
            "DOWNLOAD_MODELS",
            "Qwen/Qwen3-TTS-12Hz-1.7B-Base,Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign,Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
        )

        # Patch ProjectConfig.get_settings
        from config import ProjectConfig, ProjectSettings

        settings = ProjectSettings(
            MODELS_DIR=models_dir,
            VOICES_DIR=voices_dir,
            OUTPUT_DIR=output_dir,
            APP_DIR=app_dir,
            RESOURCES_DIR=resources_dir,
            DOWNLOAD_MODELS="Qwen/Qwen3-TTS-12Hz-1.7B-Base,Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign,Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
        )

        def mock_get_settings():
            return settings

        # We must patch get_settings on the class
        monkeypatch.setattr("config.ProjectConfig.get_settings", mock_get_settings)

        # Update the class attribute directly
        ProjectConfig._settings = settings
        ProjectConfig._logger = None

        # Also make sure the environment variables are set
        monkeypatch.setenv("MODELS_DIR", str(models_dir))
        monkeypatch.setenv("VOICES_DIR", str(voices_dir))
        monkeypatch.setenv("OUTPUT_DIR", str(output_dir))
        monkeypatch.setenv("APP_DIR", str(app_dir))
        monkeypatch.setenv("RESOURCES_DIR", str(resources_dir))
