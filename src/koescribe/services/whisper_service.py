from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from faster_whisper.utils import download_model
from platformdirs import user_data_dir


MODEL_CATALOG: list[dict[str, Any]] = [
    {
        "model_id": "tiny",
        "name": "Tiny",
        "download_size": "~75 MB",
        "speed": "Fastest",
        "accuracy": "Basic",
        "description": (
            "Best for quick testing and computers "
            "with very limited resources."
        ),
        "recommended_vram": "Less than 1 GB",
    },
    {
        "model_id": "base",
        "name": "Base",
        "download_size": "~145 MB",
        "speed": "Very fast",
        "accuracy": "Good",
        "description": (
            "A lightweight model suitable for CPU transcription "
            "and entry-level GPUs."
        ),
        "recommended_vram": "About 1 GB",
    },
    {
        "model_id": "small",
        "name": "Small",
        "download_size": "~500 MB",
        "speed": "Fast",
        "accuracy": "Very good",
        "description": (
            "A strong balance of speed, accuracy and multilingual "
            "dictation quality."
        ),
        "recommended_vram": "About 2 GB",
    },
    {
        "model_id": "medium",
        "name": "Medium",
        "download_size": "~1.5 GB",
        "speed": "Moderate",
        "accuracy": "Excellent",
        "description": (
            "Higher transcription accuracy with increased "
            "memory usage and processing time."
        ),
        "recommended_vram": "About 5 GB",
    },
    {
        "model_id": "large-v3",
        "name": "Large v3",
        "download_size": "~3 GB",
        "speed": "Slow",
        "accuracy": "Highest",
        "description": (
            "The highest multilingual Whisper accuracy, designed "
            "for computers with powerful GPUs."
        ),
        "recommended_vram": "10 GB or more",
    },
    {
        "model_id": "distil-large-v3",
        "name": "Distil Large v3",
        "download_size": "~1.5 GB",
        "speed": "Moderate",
        "accuracy": "Excellent",
        "description": (
            "A faster distilled model primarily optimized "
            "for English transcription."
        ),
        "recommended_vram": "About 4 GB",
    },
]


class WhisperService:
    """Manage faster-whisper model selection and local downloads."""

    def __init__(self) -> None:
        data_directory = Path(
            user_data_dir(
                appname="KoeScribe",
                appauthor="KoeScribe",
            )
        )

        self.models_directory = (
            data_directory / "whisper-models"
        )

        self.models_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.gpu_memory_mb = self._detect_gpu_memory_mb()
        self.recommended_model_id = (
            self._select_recommended_model()
        )

    def get_models(self) -> list[dict[str, Any]]:
        models: list[dict[str, Any]] = []

        for model in MODEL_CATALOG:
            model_data = model.copy()
            model_id = str(model_data["model_id"])

            model_data["downloaded"] = self.is_downloaded(
                model_id
            )

            model_data["local_path"] = str(
                self.get_model_path(model_id)
            )

            model_data["recommended"] = (
                model_id == self.recommended_model_id
            )

            if model_data["recommended"]:
                model_data["recommendation_reason"] = (
                    self.get_recommendation_reason()
                )
            else:
                model_data["recommendation_reason"] = ""

            models.append(model_data)

        return models

    def get_model_path(self, model_id: str) -> Path:
        self._validate_model_id(model_id)

        return self.models_directory / model_id

    def is_downloaded(self, model_id: str) -> bool:
        model_path = self.get_model_path(model_id)

        required_files = [
            model_path / "model.bin",
            model_path / "config.json",
            model_path / "tokenizer.json",
        ]

        return all(
            path.is_file()
            for path in required_files
        )

    def download(self, model_id: str) -> Path:
        self._validate_model_id(model_id)

        model_path = self.get_model_path(model_id)

        model_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        downloaded_path = download_model(
            model_id,
            output_dir=str(model_path),
        )

        final_path = Path(downloaded_path)

        if not self.is_downloaded(model_id):
            raise RuntimeError(
                f"The {model_id} model download did not complete."
            )

        return final_path

    def get_recommended_model(self) -> dict[str, Any]:
        for model in self.get_models():
            if model["recommended"]:
                return model

        raise RuntimeError(
            "No recommended Whisper model is configured."
        )

    def get_recommendation_reason(self) -> str:
        if self.gpu_memory_mb is None:
            return (
                "Recommended because no compatible NVIDIA GPU "
                "was detected. This model works well on CPU."
            )

        gpu_memory_gb = self.gpu_memory_mb / 1024

        return (
            f"Recommended for the detected "
            f"{gpu_memory_gb:.1f} GB NVIDIA GPU, "
            f"while leaving memory available for LM Studio."
        )

    def _select_recommended_model(self) -> str:
        if self.gpu_memory_mb is None:
            return "base"

        if self.gpu_memory_mb < 2048:
            return "base"

        if self.gpu_memory_mb < 10240:
            return "small"

        if self.gpu_memory_mb < 16384:
            return "medium"

        return "large-v3"

    def _detect_gpu_memory_mb(self) -> int | None:
        nvidia_smi = shutil.which("nvidia-smi")

        if nvidia_smi is None:
            return None

        try:
            result = subprocess.run(
                [
                    nvidia_smi,
                    "--query-gpu=memory.total",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return None

        if result.returncode != 0:
            return None

        first_gpu = result.stdout.strip().splitlines()

        if not first_gpu:
            return None

        try:
            return int(first_gpu[0].strip())
        except ValueError:
            return None

    def _validate_model_id(self, model_id: str) -> None:
        valid_model_ids = {
            str(model["model_id"])
            for model in MODEL_CATALOG
        }

        if model_id not in valid_model_ids:
            raise ValueError(
                f"Unsupported Whisper model: {model_id}"
            )