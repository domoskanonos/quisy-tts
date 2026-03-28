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
    description: str


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
        try:
            root = ElementTree.fromstring(xml_string)
        except ElementTree.ParseError as e:
            raise ValueError(f"Invalid XML syntax: {e}")

        if root.tag != "speak":
            raise ValueError("Root tag must be <speak>")

        tasks = []

        # Flache Struktur prüfen (kein Nesting)
        for child in root:
            if child.tag == "speaker":
                name = child.get("name")
                if not name:
                    raise ValueError("Speaker tag missing 'name' attribute")

                # Treat 'name' as voice_id
                voice = self.voice_service.get_voice(name)
                if not voice:
                    raise ValueError(f"Unknown speaker ID: {name}")

                text = child.text or ""
                parts = re.split(r"\[(.*?)\]", text)
                for i, part in enumerate(parts):
                    if i % 2 == 0:
                        if part:
                            tasks.append(TextTask(text=part, speaker=voice["id"]))
                    else:
                        tasks.append(SoundEffectTask(description=part))

            elif child.tag == "break":
                time_val = child.get("time")
                strength = child.get("strength")

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
                raise ValueError(f"Unsupported tag: {child.tag}")

        return tasks
