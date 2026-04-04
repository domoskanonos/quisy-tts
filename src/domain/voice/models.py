from dataclasses import dataclass
from typing import Optional


@dataclass
class Voice:
    voice_id: str
    name: str
    example_text: str
    instruct: Optional[str]
    language: str
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row: dict) -> "Voice":
        return cls(
            voice_id=row["voice_id"],
            name=row["name"],
            example_text=row["example_text"],
            instruct=row.get("instruct"),
            language=row["language"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def get_filename(voice_id: str) -> str:
        return f"voice_{voice_id}.wav"
