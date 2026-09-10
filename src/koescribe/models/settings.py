from __future__ import annotations

from typing import TypedDict


class AppSettings(TypedDict, total=False):
    setup_complete: bool
    whisper_model_id: str
    lm_studio_enabled: bool
    lm_studio_url: str
    lm_studio_model_id: str
    microphone_id: str
