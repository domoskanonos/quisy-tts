from xml.etree import ElementTree
from typing import List, Union
from pydantic import BaseModel
from src.core.interfaces import VoiceServiceInterface
import re


class TextTask(BaseModel):
    text: str
    speaker: str


class BreakTask(BaseModel):
    duration_ms: int


Task = Union[TextTask, BreakTask]


class SSMLProcessor:
    def __init__(self, voice_service: VoiceServiceInterface):
        self.voice_service = voice_service

    def parse(self, xml_string: str) -> List[Task]:
        try:
            root = ElementTree.fromstring(xml_string)
        except ElementTree.ParseError as e:
            raise ValueError(f"Invalid XML syntax: {e}")

        if root.tag != "speak":
            raise ValueError("Root tag must be <speak>")

        if root.text and root.text.strip():
            raise ValueError("Text found without a speaker")

        tasks = []

        def _process_element(element, current_speaker: str | None):
            # Skip comments
            if element.tag == "!--":
                return

            # Process tag logic
            if element.tag == "speaker":
                name = element.get("name")
                if not name:
                    raise ValueError("Speaker tag missing 'name' attribute")
                voice = self.voice_service.get_voice(name)
                if not voice:
                    raise ValueError(f"Unknown speaker ID: {name}")
                current_speaker = voice["voice_id"]

                # Process text within this tag
                if element.text and element.text.strip():
                    if current_speaker is None:
                        raise ValueError("Text found without a speaker")
                    tasks.append(TextTask(text=element.text.strip(), speaker=current_speaker))

                # Recurse for children
                for child in element:
                    _process_element(child, current_speaker)

            elif element.tag == "break":
                time_val = element.get("time")
                if time_val:
                    if not re.match(r"^\d+(\.\d+)?(ms|s)$", time_val):
                        raise ValueError(f"Invalid break time format: {time_val}")
                    value = float(re.findall(r"\d+\.?\d*", time_val)[0])
                    unit = re.findall(r"ms|s", time_val)[0]
                    duration_ms = int(value * 1000 if unit == "s" else value)
                    tasks.append(BreakTask(duration_ms=duration_ms))
                else:
                    raise ValueError("Break tag missing 'time' attribute")
            else:
                raise ValueError(f"Unsupported tag: {element.tag}")

            # Process tail (text after tag)
            if element.tail and element.tail.strip():
                if current_speaker is None:
                    raise ValueError("Text found without a speaker")
                tasks.append(TextTask(text=element.tail.strip(), speaker=current_speaker))

        # Start traversal from root
        for child in root:
            _process_element(child, None)

        return tasks
