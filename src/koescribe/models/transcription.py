from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class TranscriptionResult:
    text: str
    language: str
    language_probability: float
    duration: float
    device: str
    compute_type: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
