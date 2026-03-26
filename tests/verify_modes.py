import sys
from pathlib import Path
import pytest


# Add src to path
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from config import ProjectConfig
from schemas import TTSParams

# Load QwenTextToSpeech directly from source to avoid importing the engine
# package which can trigger circular imports during test initialization.
import importlib.util
from pathlib import Path as _Path

_svc_path = _Path(__file__).resolve().parent.parent / "src" / "engine" / "qwen.py"
_spec = importlib.util.spec_from_file_location("engine.qwen", str(_svc_path))
assert _spec is not None and _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
# Provide a lightweight 'services' package in sys.modules to avoid importing
# the real services package (which triggers circular imports during test
# initialization). We only need the submodules used by qwen.py.
import types
import sys as _sys

services_pkg = types.ModuleType("services")

# Minimal text_splitter module with get_text_splitter()
text_splitter_mod = types.ModuleType("services.text_splitter")


def _dummy_get_text_splitter():
    return None


text_splitter_mod.get_text_splitter = _dummy_get_text_splitter

# Minimal voice_service module with a VoiceService stub
voice_service_mod = types.ModuleType("services.voice_service")


class _DummyVoiceService:
    def __init__(self, *a, **k):
        pass

    def get_voice(self, *_):
        return None


voice_service_mod.VoiceService = _DummyVoiceService

services_pkg.text_splitter = text_splitter_mod
services_pkg.voice_service = voice_service_mod

_sys.modules["services"] = services_pkg
_sys.modules["services.text_splitter"] = text_splitter_mod
_sys.modules["services.voice_service"] = voice_service_mod

_spec.loader.exec_module(_mod)  # type: ignore[attr-defined]
QwenTextToSpeech = getattr(_mod, "QwenTextToSpeech")


@pytest.mark.asyncio
async def test_modes() -> None:
    logger = ProjectConfig.get_logger()
    settings = ProjectConfig.get_settings()
    tts = QwenTextToSpeech()

    # Test for both 1.7B and 0.6B
    for size in ["1.7B", "0.6B"]:
        logger.info(f"=== Testing Model Size: {size} ===")

        # 1. Base Mode
        logger.info(f"--- Testing Base Mode ({size}) ---")
        output_base = settings.OUTPUT_DIR / f"test_base_{size}.wav"
        params_base = TTSParams(mode="base", model_size=size, language="german")
        await tts.generate_and_save("This is a test of voice cloning.", str(output_base), params_base)

        # 2. VoiceDesign Mode
        if size != "0.6B":
            logger.info(f"--- Testing VoiceDesign Mode ({size}) ---")
            output_design = settings.OUTPUT_DIR / f"test_design_{size}.wav"
            params_design = TTSParams(
                mode="voice_design",
                model_size=size,
                instruct="Generate a friendly voice.",
                language="german",
            )
            await tts.generate_and_save("Hello, this is a designed voice.", str(output_design), params_design)
        else:
            logger.info(f"--- Skipping VoiceDesign Mode ({size}) - Not Supported ---")

        # 3. CustomVoice Mode
        logger.info(f"--- Testing CustomVoice Mode ({size}) ---")
        output_custom = settings.OUTPUT_DIR / f"test_custom_{size}.wav"
        params_custom = TTSParams(mode="custom_voice", model_size=size, speaker="eric", language="german")
        await tts.generate_and_save("Dies ist ein Test mit Eric.", str(output_custom), params_custom)

    logger.info("Verification complete. Check the output directory.")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_modes())
