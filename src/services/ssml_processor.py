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
        # Replace [text] with <sfx>text</sfx> to make it a valid tag
        xml_string = re.sub(r"\[(.*?)\]", r"<sfx>\1</sfx>", xml_string)

        try:
            root = ElementTree.fromstring(xml_string)
        except ElementTree.ParseError as e:
            raise ValueError(f"Invalid XML syntax: {e}")

        if root.tag != "speak":
            raise ValueError("Root tag must be <speak>")

        tasks = []

        def _process_element(element, current_speaker: str | None):
            if element.tag == "speaker":
                name = element.get("name")
                if not name:
                    raise ValueError("Speaker tag missing 'name' attribute")
                voice = self.voice_service.get_voice(name)
                if not voice:
                    raise ValueError(f"Unknown speaker ID: {name}")

                # Process text in this tag
                if element.text:
                    tasks.append(TextTask(text=element.text, speaker=voice["id"]))

                # Recurse for children (like <sfx>)
                for child in element:
                    _process_element(child, voice["id"])

                # Process tail (text after tag)
                if element.tail:
                    # Tail text is outside of speaker, so no speaker ID
                    # We might need to split it if it has [text] or other things,
                    # but <sfx> tags are already handled.
                    # Simple approach: add as text task without speaker?
                    # Actually, the user shouldn't have raw text outside tags.
                    pass

            elif element.tag == "sfx":
                tasks.append(SoundEffectTask(description=element.text or ""))

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
