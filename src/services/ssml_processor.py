from xml.etree import ElementTree
from typing import List, Union
from pydantic import BaseModel
from services.voice_service import VoiceService
import re


class TextTask(BaseModel):
    text: str
    speaker: str


class BreakTask(BaseModel):
    duration_ms: int


class SoundEffectTask(BaseModel):
    """
    Represents a sound effect task.
    NOTE: Descriptions MUST be in English for best results with the AudioLDM2 model.
    """

    description: str
    duration_s: float = 5.0


Task = Union[TextTask, BreakTask, SoundEffectTask]

STRENGTH_TO_MS = {
    "none": 0,
    "x-weak": 50,
    "weak": 100,
    "medium": 250,
    "strong": 500,
    "x-strong": 750,
}


class SSMLProcessor:
    def __init__(self, voice_service: VoiceService):
        self.voice_service = voice_service

    def parse(self, xml_string: str) -> List[Task]:
        # Replace [text] or [text{3s}] with <sfx duration="3">text</sfx>
        def _sfx_sub(match):
            description = match.group(1)
            duration = match.group(2) if match.group(2) else "5.0"
            return f'<sfx duration="{duration}">{description}</sfx>'

        xml_string = re.sub(r"\[(.*?)(?:\{(\d+)s\})?\]", _sfx_sub, xml_string)

        try:
            root = ElementTree.fromstring(xml_string)
        except ElementTree.ParseError as e:
            raise ValueError(f"Invalid XML syntax: {e}")

        if root.tag != "speak":
            raise ValueError("Root tag must be <speak>")

        tasks = []

        def _process_element(element, current_speaker: str | None):
            if element.tag == "speaker":
                # ... (rest of speaker processing unchanged)
                name = element.get("name")
                if not name:
                    raise ValueError("Speaker tag missing 'name' attribute")
                voice = self.voice_service.get_voice(name)
                if not voice:
                    raise ValueError(f"Unknown speaker ID: {name}")

                # Process text in this tag
                if element.text and element.text.strip():
                    tasks.append(TextTask(text=element.text.strip(), speaker=voice["voice_id"]))

                # Recurse for children (like <sfx>)
                for child in element:
                    _process_element(child, voice["voice_id"])

                # Process tail (text after tag)
                if element.tail:
                    pass

            elif element.tag == "sfx":
                duration = float(element.get("duration", 5.0))
                tasks.append(SoundEffectTask(description=element.text or "", duration_s=duration))

            elif element.tag == "break":
                time_val = element.get("time")
                strength = element.get("strength")
                if time_val:
                    if not re.match(r"^\d+(\.\d+)?(ms|s)$", time_val):
                        raise ValueError(f"Invalid break time format: {time_val}")
                    value = float(re.findall(r"\d+\.?\d*", time_val)[0])
                    unit = re.findall(r"ms|s", time_val)[0]
                    duration_ms = int(value * 1000 if unit == "s" else value)
                    tasks.append(BreakTask(duration_ms=duration_ms))
                elif strength:
                    if strength not in STRENGTH_TO_MS:
                        raise ValueError(f"Invalid break strength: {strength}")
                    tasks.append(BreakTask(duration_ms=STRENGTH_TO_MS[strength]))
                else:
                    raise ValueError("Break tag missing 'time' or 'strength' attribute")
            else:
                raise ValueError(f"Unsupported tag: {element.tag}")

        for child in root:
            _process_element(child, None)

        return tasks
