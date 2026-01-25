import sys
from pathlib import Path


# Add src to path
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from project.config import ProjectConfig
from project.engine.qwen import QwenTextToSpeech
from project.schemas import TTSParams


def test_modes() -> None:
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
        tts.generate_and_save(
            "This is a test of voice cloning.", str(output_base), params_base
        )

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
            tts.generate_and_save(
                "Hello, this is a designed voice.", str(output_design), params_design
            )
        else:
            logger.info(f"--- Skipping VoiceDesign Mode ({size}) - Not Supported ---")

        # 3. CustomVoice Mode
        logger.info(f"--- Testing CustomVoice Mode ({size}) ---")
        output_custom = settings.OUTPUT_DIR / f"test_custom_{size}.wav"
        params_custom = TTSParams(
            mode="custom_voice", model_size=size, speaker="eric", language="german"
        )
        tts.generate_and_save(
            "Dies ist ein Test mit Eric.", str(output_custom), params_custom
        )

    logger.info("Verification complete. Check the output directory.")


if __name__ == "__main__":
    test_modes()
