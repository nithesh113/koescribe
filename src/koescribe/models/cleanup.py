from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CleanupResult:
    text: str
    model_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
