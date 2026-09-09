from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, QObject, QThread, Signal, Slot

from koescribe.services.lm_studio_service import (
    DEFAULT_LM_STUDIO_URL,
    LMStudioService,
)
from koescribe.services.system_service import SystemService
from koescribe.services.settings_service import SettingsService
from koescribe.services.whisper_service import WhisperService


class SystemDetectionWorker(QThread):
    completed = Signal(object)
    failed = Signal(str)

    def run(self) -> None:
        try:
            information = SystemService().detect()
            self.completed.emit(information.to_dict())
        except Exception as error:
            self.failed.emit(str(error))


class WhisperDownloadWorker(QThread):
    completed = Signal(str, str)
    failed = Signal(str, str)

    def __init__(self, model_id: str) -> None:
        super().__init__()
        self.model_id = model_id

    def run(self) -> None:
        try:
            path = WhisperService().download(self.model_id)
            self.completed.emit(self.model_id, str(path))
        except Exception as error:
            self.failed.emit(self.model_id, str(error))


class LMStudioCheckWorker(QThread):
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url

    def run(self) -> None:
        try:
            result = LMStudioService(self.base_url).check_connection()
            self.completed.emit(result.to_dict())
        except Exception as error:
            self.failed.emit(str(error))


class SetupController(QObject):
    checksChanged = Signal()
    systemInfoChanged = Signal()
    scanningChanged = Signal()
    errorChanged = Signal()
    whisperModelsChanged = Signal()
    selectedModelChanged = Signal()
    downloadStateChanged = Signal()
    lmStudioChanged = Signal()
    setupCompleteChanged = Signal()
    setupFinished = Signal()

    def __init__(self) -> None:
        super().__init__()

        self._checks: list[dict[str, Any]] = []
        self._system_info: dict[str, Any] = {}
        self._scanning = False
        self._error_message = ""
        self._system_worker: SystemDetectionWorker | None = None

        self._settings_service = SettingsService()
        self._settings = self._settings_service.load()
        self._setup_complete = bool(
            self._settings.get("setup_complete", False)
        )

        self._whisper_service = WhisperService()
        self._whisper_models = self._whisper_service.get_models()
        recommendation = self._whisper_service.get_recommended_model()
        saved_whisper_model_id = str(
            self._settings.get("whisper_model_id", "")
        )
        whisper_model_ids = {
            str(model["model_id"]) for model in self._whisper_models
        }
        self._selected_model_id = (
            saved_whisper_model_id
            if saved_whisper_model_id in whisper_model_ids
            else str(recommendation["model_id"])
        )

        self._downloading = False
        self._download_status = ""
        self._downloading_model_id = ""
        self._download_worker: WhisperDownloadWorker | None = None

        self._lm_studio_url = str(
            self._settings.get("lm_studio_url", DEFAULT_LM_STUDIO_URL)
        )
        self._lm_studio_enabled = bool(
            self._settings.get("lm_studio_enabled", True)
        )
        self._lm_studio_checking = False
        self._lm_studio_connected = False
        self._lm_studio_status = "Not checked"
        self._lm_studio_message = ""
        self._lm_studio_models: list[dict[str, Any]] = []
        self._selected_lm_studio_model_id = str(
            self._settings.get("lm_studio_model_id", "")
        )
        self._lm_studio_worker: LMStudioCheckWorker | None = None

    @Property("QVariantList", notify=checksChanged)
    def checks(self) -> list[dict[str, Any]]:
        return self._checks

    @Property("QVariantMap", notify=systemInfoChanged)
    def systemInfo(self) -> dict[str, Any]:
        return self._system_info

    @Property(bool, notify=scanningChanged)
    def scanning(self) -> bool:
        return self._scanning

    @Property(str, notify=errorChanged)
    def errorMessage(self) -> str:
        return self._error_message

    @Property(bool, notify=checksChanged)
    def hasBlockingIssues(self) -> bool:
        return any(
            check.get("required", True) and not check.get("ready", False)
            for check in self._checks
        )

    @Property(str, notify=systemInfoChanged)
    def systemSummary(self) -> str:
        if not self._system_info:
            return "System information not available"

        operating_system = self._system_info.get(
            "operating_system_version", "Unknown system"
        )
        architecture = self._system_info.get(
            "architecture", "Unknown architecture"
        )
        return f"{operating_system} · {architecture}"

    @Property("QVariantList", notify=whisperModelsChanged)
    def whisperModels(self) -> list[dict[str, Any]]:
        return self._whisper_models

    @Property(str, notify=selectedModelChanged)
    def selectedModelId(self) -> str:
        return self._selected_model_id

    @Property("QVariantMap", notify=selectedModelChanged)
    def selectedModel(self) -> dict[str, Any]:
        for model in self._whisper_models:
            if model["model_id"] == self._selected_model_id:
                return model
        return {}

    @Property(str, notify=whisperModelsChanged)
    def recommendedModelId(self) -> str:
        return self._whisper_service.recommended_model_id

    @Property(bool, notify=downloadStateChanged)
    def downloading(self) -> bool:
        return self._downloading

    @Property(str, notify=downloadStateChanged)
    def downloadStatus(self) -> str:
        return self._download_status

    @Property(str, notify=downloadStateChanged)
    def downloadingModelId(self) -> str:
        return self._downloading_model_id

    @Property(bool, notify=selectedModelChanged)
    def selectedModelDownloaded(self) -> bool:
        return bool(self.selectedModel.get("downloaded", False))

    @Property(str, notify=lmStudioChanged)
    def lmStudioUrl(self) -> str:
        return self._lm_studio_url

    @Property(bool, notify=lmStudioChanged)
    def lmStudioEnabled(self) -> bool:
        return self._lm_studio_enabled

    @Property(bool, notify=lmStudioChanged)
    def lmStudioChecking(self) -> bool:
        return self._lm_studio_checking

    @Property(bool, notify=lmStudioChanged)
    def lmStudioConnected(self) -> bool:
        return self._lm_studio_connected

    @Property(str, notify=lmStudioChanged)
    def lmStudioStatus(self) -> str:
        return self._lm_studio_status

    @Property(str, notify=lmStudioChanged)
    def lmStudioMessage(self) -> str:
        return self._lm_studio_message

    @Property("QVariantList", notify=lmStudioChanged)
    def lmStudioModels(self) -> list[dict[str, Any]]:
        return self._lm_studio_models

    @Property(str, notify=lmStudioChanged)
    def selectedLmStudioModelId(self) -> str:
        return self._selected_lm_studio_model_id

    @Property(bool, notify=lmStudioChanged)
    def lmStudioReady(self) -> bool:
        return (
            not self._lm_studio_enabled
            or (
                self._lm_studio_connected
                and bool(self._selected_lm_studio_model_id)
            )
        )

    @Property(bool, notify=setupCompleteChanged)
    def setupComplete(self) -> bool:
        return self._setup_complete

    @Slot()
    def scanSystem(self) -> None:
        if self._system_worker and self._system_worker.isRunning():
            return

        self._set_scanning(True)
        self._set_error_message("")
        self._system_worker = SystemDetectionWorker()
        self._system_worker.completed.connect(self._apply_system_results)
        self._system_worker.failed.connect(self._apply_system_error)
        self._system_worker.finished.connect(self._system_worker_finished)
        self._system_worker.start()

    @Slot(str)
    def selectWhisperModel(self, model_id: str) -> None:
        if self._downloading:
            return

        valid_ids = {
            str(model["model_id"]) for model in self._whisper_models
        }
        if model_id not in valid_ids:
            return

        self._selected_model_id = model_id
        self._download_status = ""
        self.selectedModelChanged.emit()
        self.downloadStateChanged.emit()

    @Slot()
    def downloadSelectedModel(self) -> None:
        self.downloadWhisperModel(self._selected_model_id)

    @Slot(str)
    def downloadWhisperModel(self, model_id: str) -> None:
        if self._downloading:
            return

        valid_ids = {
            str(model["model_id"]) for model in self._whisper_models
        }
        if model_id not in valid_ids:
            self._download_status = f"Unknown Whisper model: {model_id}"
            self.downloadStateChanged.emit()
            return

        self._selected_model_id = model_id
        self._downloading = True
        self._downloading_model_id = model_id
        self._download_status = f"Downloading {model_id} model..."

        self.selectedModelChanged.emit()
        self.downloadStateChanged.emit()

        self._download_worker = WhisperDownloadWorker(model_id)
        self._download_worker.completed.connect(self._download_completed)
        self._download_worker.failed.connect(self._download_failed)
        self._download_worker.finished.connect(self._download_worker_finished)
        self._download_worker.start()

    @Slot()
    def refreshWhisperModels(self) -> None:
        self._whisper_models = self._whisper_service.get_models()
        self.whisperModelsChanged.emit()
        self.selectedModelChanged.emit()

    @Slot(str)
    def checkLmStudio(self, base_url: str) -> None:
        if self._lm_studio_worker and self._lm_studio_worker.isRunning():
            return

        self._lm_studio_checking = True
        self._lm_studio_status = "Connecting"
        self._lm_studio_message = "Testing the LM Studio local server..."
        self.lmStudioChanged.emit()

        self._lm_studio_worker = LMStudioCheckWorker(base_url)
        self._lm_studio_worker.completed.connect(
            self._apply_lm_studio_result
        )
        self._lm_studio_worker.failed.connect(
            self._apply_lm_studio_error
        )
        self._lm_studio_worker.finished.connect(
            self._lm_studio_worker_finished
        )
        self._lm_studio_worker.start()

    @Slot(str)
    def selectLmStudioModel(self, model_id: str) -> None:
        valid_ids = {
            str(model["model_id"]) for model in self._lm_studio_models
        }
        if model_id in valid_ids:
            self._selected_lm_studio_model_id = model_id
            self.lmStudioChanged.emit()

    @Slot(bool)
    def setLmStudioEnabled(self, enabled: bool) -> None:
        self._lm_studio_enabled = enabled
        self.lmStudioChanged.emit()

    @Slot(str)
    def finishSetup(self, microphone_id: str) -> None:
        self._settings = {
            "setup_complete": True,
            "whisper_model_id": self._selected_model_id,
            "lm_studio_enabled": self._lm_studio_enabled,
            "lm_studio_url": self._lm_studio_url,
            "lm_studio_model_id": self._selected_lm_studio_model_id,
            "microphone_id": microphone_id,
        }
        self._settings_service.save(self._settings)

        if not self._setup_complete:
            self._setup_complete = True
            self.setupCompleteChanged.emit()

        self.setupFinished.emit()

    @Slot()
    def resetSetup(self) -> None:
        self._setup_complete = False
        self._settings["setup_complete"] = False
        self._settings_service.save(self._settings)
        self.setupCompleteChanged.emit()

    @Slot(object)
    def _apply_system_results(self, information: dict[str, Any]) -> None:
        self._system_info = information
        self._checks = information.get("checks", [])
        self.systemInfoChanged.emit()
        self.checksChanged.emit()
        self._set_scanning(False)

    @Slot(str)
    def _apply_system_error(self, message: str) -> None:
        self._set_error_message(f"System check failed: {message}")
        self._set_scanning(False)

    @Slot()
    def _system_worker_finished(self) -> None:
        if self._system_worker:
            self._system_worker.deleteLater()
            self._system_worker = None

    @Slot(str, str)
    def _download_completed(self, model_id: str, path: str) -> None:
        self._downloading = False
        self._downloading_model_id = ""
        self._download_status = f"{model_id} is ready."
        self._whisper_models = self._whisper_service.get_models()

        self.whisperModelsChanged.emit()
        self.selectedModelChanged.emit()
        self.downloadStateChanged.emit()
        print(f"Whisper model downloaded to: {path}")

    @Slot(str, str)
    def _download_failed(self, model_id: str, message: str) -> None:
        self._downloading = False
        self._downloading_model_id = ""
        self._download_status = f"Could not download {model_id}: {message}"
        self.downloadStateChanged.emit()

    @Slot()
    def _download_worker_finished(self) -> None:
        if self._download_worker:
            self._download_worker.deleteLater()
            self._download_worker = None

    @Slot(object)
    def _apply_lm_studio_result(self, result: dict[str, Any]) -> None:
        self._lm_studio_checking = False
        self._lm_studio_connected = bool(result.get("connected", False))
        self._lm_studio_status = str(result.get("status", "Unknown"))
        self._lm_studio_message = str(result.get("message", ""))
        self._lm_studio_url = str(
            result.get("base_url", DEFAULT_LM_STUDIO_URL)
        )
        self._lm_studio_models = result.get("models", [])

        valid_ids = {
            str(model["model_id"]) for model in self._lm_studio_models
        }
        if self._selected_lm_studio_model_id not in valid_ids:
            self._selected_lm_studio_model_id = (
                str(self._lm_studio_models[0]["model_id"])
                if self._lm_studio_models
                else ""
            )

        self.lmStudioChanged.emit()

    @Slot(str)
    def _apply_lm_studio_error(self, message: str) -> None:
        self._lm_studio_checking = False
        self._lm_studio_connected = False
        self._lm_studio_status = "Error"
        self._lm_studio_message = message
        self._lm_studio_models = []
        self._selected_lm_studio_model_id = ""
        self.lmStudioChanged.emit()

    @Slot()
    def _lm_studio_worker_finished(self) -> None:
        if self._lm_studio_worker:
            self._lm_studio_worker.deleteLater()
            self._lm_studio_worker = None

    def _set_scanning(self, scanning: bool) -> None:
        if self._scanning != scanning:
            self._scanning = scanning
            self.scanningChanged.emit()

    def _set_error_message(self, message: str) -> None:
        if self._error_message != message:
            self._error_message = message
            self.errorChanged.emit()
