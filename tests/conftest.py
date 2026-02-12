"""Pytest configuration and fixtures."""

import sys
from unittest.mock import MagicMock

import pytest


def pytest_configure(config):
    """Configure pytest environment."""
    # 1. Mock vLLM before any imports
    # We need to mock the entire vllm package structure that is used
    vllm_mock = MagicMock()
    vllm_mock.__version__ = "0.7.3"

    # Mock LLM class
    class MockLLM:
        def __init__(self, *args, **kwargs):
            pass

        def generate(self, *args, **kwargs):
            # Return a structure that matches what QwenVLLMBackend expects
            # It expects a list of RequestOutput objects
            mock_output = MagicMock()
            # output.multimodal_output["audio"]
            mock_output.multimodal_output = {
                "audio": __import__("torch").zeros(1, 24000),
                "sr": MagicMock(item=lambda: 24000),
            }
            return [mock_output]

    vllm_mock.LLM = MockLLM
    vllm_mock.SamplingParams = MagicMock()

    # Apply the mock to sys.modules
    sys.modules["vllm"] = vllm_mock
    sys.modules["vllm.engine"] = MagicMock()
    sys.modules["vllm.engine.arg_utils"] = MagicMock()


@pytest.fixture(autouse=True)
def mock_system_dependencies(monkeypatch):
    """Mock system checks for all tests."""
    import subprocess

    import torch

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
