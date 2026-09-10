from __future__ import annotations

from typing import Any

from koescribe.services.audio_recording_service import AudioRecordingService
from koescribe.services.settings_service import SettingsService
from koescribe.services.text_cleanup_service import TextCleanupService
from koescribe.services.transcription_service import TranscriptionService
from PySide6.QtCore import Property, QObject, QThread, QTimer, Signal, Slot


class TranscriptionWorker(QObject):
    completed = Signal(object)
    failed = Signal(str)
    stageChanged = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        self._service = TranscriptionService()
        self._cleanup_service = TextCleanupService()
        self._settings_service = SettingsService()

    @Slot(str, str)
    def transcribe(self, audio_path: str, model_id: str) -> None:
        try:
            result = self._service.transcribe(audio_path, model_id)
            result_data = result.to_dict()
            raw_text = result.text
            result_data["raw_text"] = raw_text
            result_data["cleanup_used"] = False
            result_data["cleanup_warning"] = ""

            settings = self._settings_service.load()
            if bool(settings.get("lm_studio_enabled", False)):
                lm_model_id = str(settings.get("lm_studio_model_id", ""))
                base_url = str(
                    settings.get(
                        "lm_studio_url",
                        "http://127.0.0.1:1234/v1",
                    )
                )
                if lm_model_id:
                    self.stageChanged.emit(
                        "Cleaning",
                        "Polishing the transcription with LM Studio...",
                    )
                    try:
                        cleanup = self._cleanup_service.clean(
                            raw_text,
                            base_url,
                            lm_model_id,
                        )
                        result_data["text"] = cleanup.text
                        result_data["cleanup_used"] = True
                    except Exception as cleanup_error:  # noqa: BLE001
                        result_data["cleanup_warning"] = str(cleanup_error)
                else:
                    result_data["cleanup_warning"] = (
                        "LM Studio is enabled but no cleanup model is selected."
                    )

            self.completed.emit(result_data)
        except Exception as error:  # noqa: BLE001 - report worker errors to QML
            self.failed.emit(str(error))

    @Slot()
    def unload(self) -> None:
        self._service.unload()


class DictationController(QObject):
    stateChanged = Signal()
    transcriptionRequested = Signal(str, str)
    unloadRequested = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._audio_service = AudioRecordingService(self)
        self._settings_service = SettingsService()
        self._recording = False
        self._transcribing = False
        self._elapsed_seconds = 0
        self._status = "Ready"
        self._message = "Press the microphone button to start recording."
        self._error_message = ""
        self._recording_path = ""
        self._transcription_text = ""
        self._raw_transcription_text = ""
        self._detected_language = ""
        self._inference_device = ""
        self._cleanup_used = False
        self._cleanup_warning = ""

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

        self._transcription_thread = QThread(self)
        self._transcription_worker = TranscriptionWorker()
        self._transcription_worker.moveToThread(self._transcription_thread)
        self.transcriptionRequested.connect(self._transcription_worker.transcribe)
        self.unloadRequested.connect(self._transcription_worker.unload)
        self._transcription_worker.completed.connect(self._transcription_completed)
        self._transcription_worker.failed.connect(self._transcription_failed)
        self._transcription_worker.stageChanged.connect(self._stage_changed)
        self._transcription_thread.finished.connect(self._transcription_worker.deleteLater)
        self._transcription_thread.start()

    @Property(bool, notify=stateChanged)
    def recording(self) -> bool:
        return self._recording

    @Property(bool, notify=stateChanged)
    def transcribing(self) -> bool:
        return self._transcribing

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._recording or self._transcribing

    @Property(int, notify=stateChanged)
    def elapsedSeconds(self) -> int:
        return self._elapsed_seconds

    @Property(str, notify=stateChanged)
    def elapsedText(self) -> str:
        minutes, seconds = divmod(self._elapsed_seconds, 60)
        return f"{minutes:02d}:{seconds:02d}"

    @Property(str, notify=stateChanged)
    def status(self) -> str:
        return self._status

    @Property(str, notify=stateChanged)
    def message(self) -> str:
        return self._message

    @Property(str, notify=stateChanged)
    def errorMessage(self) -> str:
        return self._error_message

    @Property(str, notify=stateChanged)
    def recordingPath(self) -> str:
        return self._recording_path

    @Property(str, notify=stateChanged)
    def transcriptionText(self) -> str:
        return self._transcription_text

    @Property(str, notify=stateChanged)
    def rawTranscriptionText(self) -> str:
        return self._raw_transcription_text

    @Property(str, notify=stateChanged)
    def detectedLanguage(self) -> str:
        return self._detected_language

    @Property(str, notify=stateChanged)
    def inferenceDevice(self) -> str:
        return self._inference_device

    @Property(bool, notify=stateChanged)
    def cleanupUsed(self) -> bool:
        return self._cleanup_used

    @Property(str, notify=stateChanged)
    def cleanupWarning(self) -> str:
        return self._cleanup_warning

    @Slot(str)
    def startRecording(self, microphone_id: str) -> None:
        if self.busy:
            return

        try:
            path = self._audio_service.start(microphone_id)
        except (OSError, RuntimeError) as error:
            self._set_error(str(error))
            return

        self._recording = True
        self._elapsed_seconds = 0
        self._status = "Listening"
        self._message = "Speak naturally. Press Stop when you are finished."
        self._error_message = ""
        self._recording_path = str(path)
        self._transcription_text = ""
        self._raw_transcription_text = ""
        self._detected_language = ""
        self._cleanup_used = False
        self._cleanup_warning = ""
        self._timer.start()
        self.stateChanged.emit()

    @Slot()
    def stopRecording(self) -> None:
        if not self._recording:
            return

        self._timer.stop()
        try:
            path = self._audio_service.stop()
        except (OSError, RuntimeError) as error:
            self._recording = False
            self._set_error(str(error))
            return

        model_id = str(self._settings_service.load().get("whisper_model_id", ""))
        if not model_id:
            self._recording = False
            self._audio_service.discard()
            self._set_error("No Whisper model is selected. Run setup and select a model.")
            return

        self._recording = False
        self._transcribing = True
        self._status = "Transcribing"
        self._message = "Converting your speech to text locally..."
        self._recording_path = str(path)
        self.stateChanged.emit()
        self.transcriptionRequested.emit(str(path), model_id)

    @Slot()
    def cancelRecording(self) -> None:
        if self._transcribing:
            return

        self._timer.stop()
        self._audio_service.cancel()
        self._recording = False
        self._elapsed_seconds = 0
        self._recording_path = ""
        self._status = "Ready"
        self._message = "Recording cancelled and temporary audio deleted."
        self._error_message = ""
        self.stateChanged.emit()

    @Slot()
    def clearTranscription(self) -> None:
        self._transcription_text = ""
        self._raw_transcription_text = ""
        self._detected_language = ""
        self._inference_device = ""
        self._cleanup_used = False
        self._cleanup_warning = ""
        self.stateChanged.emit()

    @Slot(str, str)
    def _stage_changed(self, status: str, message: str) -> None:
        self._status = status
        self._message = message
        self.stateChanged.emit()

    @Slot()
    def shutdown(self) -> None:
        self._timer.stop()
        self._audio_service.cancel()
        self.unloadRequested.emit()
        self._transcription_thread.quit()
        self._transcription_thread.wait()

    @Slot()
    def _tick(self) -> None:
        self._elapsed_seconds += 1
        self.stateChanged.emit()

    @Slot(object)
    def _transcription_completed(self, result: dict[str, Any]) -> None:
        self._transcribing = False
        self._transcription_text = str(result.get("text", ""))
        self._raw_transcription_text = str(result.get("raw_text", self._transcription_text))
        self._detected_language = str(result.get("language", "unknown"))
        self._inference_device = str(result.get("device", "cpu"))
        self._cleanup_used = bool(result.get("cleanup_used", False))
        self._cleanup_warning = str(result.get("cleanup_warning", ""))
        self._status = "Done"
        language = self._detected_language.upper()
        device = self._inference_device.upper()
        cleanup_label = " · Polished with LM Studio" if self._cleanup_used else ""
        self._message = f"Detected {language} · Transcribed with {device}{cleanup_label}"
        self._error_message = ""
        self._recording_path = ""
        self._audio_service.discard()
        self.stateChanged.emit()

    @Slot(str)
    def _transcription_failed(self, message: str) -> None:
        self._transcribing = False
        self._recording_path = ""
        self._audio_service.discard()
        self._set_error(message)

    def _set_error(self, message: str) -> None:
        self._status = "Could not transcribe"
        self._message = "KoeScribe could not process this recording."
        self._error_message = message
        self.stateChanged.emit()
