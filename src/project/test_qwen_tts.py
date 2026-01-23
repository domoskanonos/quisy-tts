import os
import sys


# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from project.config import ProjectConfig
from project.qwen_tts_engine import QwenTextToSpeech, TTSParams


def test_qwen_tts():
    logger = ProjectConfig.get_logger()
    settings = ProjectConfig.get_settings()

    logger.info("Testing Qwen3-TTS integration...")

    # Initialize model
    tts = QwenTextToSpeech()

    # Ensure directories exist
    os.makedirs(settings.VOICES_DIR, exist_ok=True)
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

    test_text = "Hallo! Dies ist ein Test der Qwen TTS Sprachgenerierung. Es scheint jetzt korrekt zu funktionieren mit Daten-Buffern."


    test_text = """ 
    
    Hier ist eine kleine Geschichte über Mut, Freundschaft und ein ganz besonderes Abenteuer.

Der flüsternde Wald und das Glühwürmchen-Rätsel
Es war einmal ein achtjähriger Junge namens Leo, der in einem kleinen Haus am Rande des „Flüsternden Waldes“ wohnte. Die Erwachsenen sagten immer, der Wald hieße so, weil der Wind in den Blättern wie Stimmen klang. Aber Leo wusste es besser: Der Wald war magisch.

Eines Abends, als der Mond wie eine silberne Sichel am Himmel hing, klopfte etwas Kleines gegen Leos Fenster. Pling. Pling.

Leo öffnete das Fenster und herein purzelte Flitzi, ein Glühwürmchen. Doch Flitzi leuchtete nicht gelb, sondern hellblau! „Leo, du musst mir helfen!“, piepste Flitzi. „Der alte Dachs hat seinen Hausschlüssel im Funkel-Bach verloren, und ohne den Schlüssel kommt er nicht in seinen gemütlichen Bau. Aber ich kann den Weg nicht zeigen, weil mein Licht blau vor Schreck geworden ist!“

Das Abenteuer beginnt
Leo zögerte keine Sekunde. Er schlüpfte in seine Gummistiefel, schnappte sich seine Taschenlampe und folgte dem blauen Schimmer von Flitzi in den Wald.

Der Wald sah nachts ganz anders aus. Die Farne wirkten wie große, grüne Drachenflügel und die Eulen riefen sich Geheimnisse zu. „Hab keine Angst“, flüsterte Leo, eher zu sich selbst als zu Flitzi.

Nach einer Weile erreichten sie den Funkel-Bach. Das Wasser plätscherte über glatte Steine. Leo leuchtete mit seiner Taschenlampe ins Wasser. Da! Zwischen zwei silbernen Kieseln blitzte etwas Goldenes auf.
    
    
    """

    output_path = os.path.join(settings.OUTPUT_DIR, "test_qwen_output.wav")

    # Pass language
    params = TTSParams(language_id="de")

    logger.info(f"Generating audio for: '{test_text}'")
    try:
        # This will trigger initialization
        result_path = tts.generate_and_save(test_text, output_path, params)
        if result_path and os.path.exists(result_path):
            logger.info(f"Success! Audio saved to {result_path}")
        else:
            logger.error("Failed to save audio.")
    except Exception as e:
        logger.error(f"Error during generation: {e}")


if __name__ == "__main__":
    test_qwen_tts()
