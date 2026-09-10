from __future__ import annotations

from pathlib import Path
from typing import Any

from koescribe.models.transcription import TranscriptionResult
from koescribe.services.cuda_service import CudaService
from koescribe.services.whisper_service import WhisperService


class NoSpeechDetectedError(RuntimeError):
    """Raised when a valid recording contains no detectable speech."""


class TranscriptionService:
    """Lazy-load and reuse one faster-whisper model."""

    def __init__(self) -> None:
        self._whisper_service = WhisperService()
        self._model: Any | None = None
        self._loaded_model_id = ""
        self._device = ""
        self._compute_type = ""

    def transcribe(
        self,
        audio_path: str | Path,
        model_id: str,
    ) -> TranscriptionResult:
        path = Path(audio_path)
        if not path.is_file():
            raise FileNotFoundError(f"Audio file not found: {path}")

        model_path = self._whisper_service.get_model_path(model_id)
        if not self._whisper_service.is_downloaded(model_id):
            raise RuntimeError(f"The selected Whisper model '{model_id}' is not downloaded.")

        self._ensure_model(model_id, model_path)

        try:
            return self._run_transcription(path)
        except NoSpeechDetectedError:
            raise
        except Exception as cuda_error:
            if self._device != "cuda":
                raise

            self._load_model(
                model_id=model_id,
                model_path=model_path,
                device="cpu",
                compute_type="int8",
            )
            try:
                return self._run_transcription(path)
            except Exception as cpu_error:
                raise RuntimeError(
                    "CUDA transcription failed and the CPU fallback also failed. "
                    f"CUDA: {cuda_error}; CPU: {cpu_error}"
                ) from cpu_error

    def unload(self) -> None:
        self._model = None
        self._loaded_model_id = ""
        self._device = ""
        self._compute_type = ""

    def _ensure_model(self, model_id: str, model_path: Path) -> None:
        if self._model is not None and self._loaded_model_id == model_id:
            return

        cuda_service = CudaService()
        if cuda_service.detect().ready:
            try:
                cuda_service.prepare_runtime()
                self._load_model(
                    model_id=model_id,
                    model_path=model_path,
                    device="cuda",
                    compute_type="float16",
                )
                return
            except Exception:  # noqa: BLE001 - fall back when CUDA cannot load
                self.unload()

        self._load_model(
            model_id=model_id,
            model_path=model_path,
            device="cpu",
            compute_type="int8",
        )

    def _load_model(
        self,
        model_id: str,
        model_path: Path,
        device: str,
        compute_type: str,
    ) -> None:
        from faster_whisper import WhisperModel

        self._model = WhisperModel(
            str(model_path),
            device=device,
            compute_type=compute_type,
        )
        self._loaded_model_id = model_id
        self._device = device
        self._compute_type = compute_type

    def _run_transcription(self, audio_path: Path) -> TranscriptionResult:
        if self._model is None:
            raise RuntimeError("The Whisper model is not loaded.")

        segments, information = self._model.transcribe(
            str(audio_path),
            beam_size=5,
            vad_filter=True,
            condition_on_previous_text=False,
        )
        text = " ".join(
            segment.text.strip() for segment in segments if segment.text.strip()
        ).strip()

        if not text:
            raise NoSpeechDetectedError(
                "No speech was detected. Check the microphone and try again."
            )

        return TranscriptionResult(
            text=text,
            language=str(information.language or "unknown"),
            language_probability=float(information.language_probability or 0.0),
            duration=float(information.duration or 0.0),
            device=self._device,
            compute_type=self._compute_type,
        )
