from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from platformdirs import user_config_dir


class SettingsService:
    def __init__(self) -> None:
        self.path = (
            Path(user_config_dir("KoeScribe", "KoeScribe"))
            / "settings.json"
        )

    def load(self) -> dict[str, Any]:
        if not self.path.is_file():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def save(self, settings: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(settings, indent=2),
            encoding="utf-8",
        )
        temporary.replace(self.path)
