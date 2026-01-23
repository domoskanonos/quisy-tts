import os
import sys


# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from project.config import ProjectConfig
from project.qwen_tts_engine import QwenTextToSpeech, TTSParams


def test_modes():
    logger = ProjectConfig.get_logger()
    settings = ProjectConfig.get_settings()
    tts = QwenTextToSpeech()

    # 1. Test Base Mode (Voice Cloning)
    logger.info("--- Testing Base Mode (Voice Cloning) ---")
    output_base = os.path.join(settings.OUTPUT_DIR, "test_base_clone.wav")
    params_base = TTSParams(mode="base", language_id="en")
    # This will use default reference logic in generate_audio if no ref passed
    tts.generate_and_save(
        "This is a test of voice cloning in base mode.", output_base, params_base
    )

    # 2. Test VoiceDesign Mode (Instruction)
    logger.info("--- Testing VoiceDesign Mode (Instruction) ---")
    output_design = os.path.join(settings.OUTPUT_DIR, "test_voice_design.wav")
    params_design = TTSParams(
        mode="voice_design",
        language_id="en",
        instruct="Generate a voice of a middle-aged man with a deep and calm tone.",
    )
    tts.generate_and_save(
        "This is a test of voice design with natural language instructions.",
        output_design,
        params_design,
    )

    # 3. Test CustomVoice Mode (Speaker ID)
    logger.info("--- Testing CustomVoice Mode (Speaker ID) ---")
    output_custom = os.path.join(settings.OUTPUT_DIR, "test_custom_voice.wav")
    params_custom = TTSParams(mode="custom_voice", language_id="de", speaker="eric")
    tts.generate_and_save(
        "Dies ist ein Test mit einer spezifischen Sprecher-ID.",
        output_custom,
        params_custom,
    )

    logger.info("Verification complete. Check the output directory for results.")


if __name__ == "__main__":
    test_modes()
