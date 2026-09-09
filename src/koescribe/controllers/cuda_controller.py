from __future__ import annotations

from typing import Any

from koescribe.services.cuda_service import CudaService
from PySide6.QtCore import Property, QObject, QThread, Signal, Slot


class CudaWorker(QThread):
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, install: bool = False) -> None:
        super().__init__()
        self.install = install

    def run(self) -> None:
        try:
            service = CudaService()
            result = service.install() if self.install else service.detect()
            self.completed.emit(result.to_dict())
        except Exception as error:  # noqa: BLE001 - report worker failures to QML
            self.failed.emit(str(error))


class CudaController(QObject):
    stateChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._result: dict[str, Any] = {
            "ready": False,
            "status": "Not checked",
            "message": "Checking CUDA acceleration...",
            "missing": [],
            "install_supported": False,
            "install_command": "",
        }
        self._busy = False
        self._installing = False
        self._error_message = ""
        self._worker: CudaWorker | None = None

    @Property(bool, notify=stateChanged)
    def ready(self) -> bool:
        return bool(self._result.get("ready", False))

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(bool, notify=stateChanged)
    def installing(self) -> bool:
        return self._installing

    @Property(str, notify=stateChanged)
    def status(self) -> str:
        return str(self._result.get("status", "Not checked"))

    @Property(str, notify=stateChanged)
    def message(self) -> str:
        return str(self._result.get("message", ""))

    @Property(str, notify=stateChanged)
    def errorMessage(self) -> str:
        return self._error_message

    @Property(bool, notify=stateChanged)
    def canInstall(self) -> bool:
        return (
            bool(self._result.get("install_supported", False)) and not self.ready and not self._busy
        )

    @Property(str, notify=stateChanged)
    def installCommand(self) -> str:
        return str(self._result.get("install_command", ""))

    @Slot()
    def scan(self) -> None:
        self._start_worker(install=False)

    @Slot()
    def install(self) -> None:
        if not self.canInstall:
            return
        self._start_worker(install=True)

    def _start_worker(self, install: bool) -> None:
        if self._worker and self._worker.isRunning():
            return

        self._busy = True
        self._installing = install
        self._error_message = ""
        self.stateChanged.emit()

        self._worker = CudaWorker(install=install)
        self._worker.completed.connect(self._completed)
        self._worker.failed.connect(self._failed)
        self._worker.finished.connect(self._worker_finished)
        self._worker.start()

    @Slot(object)
    def _completed(self, result: dict[str, Any]) -> None:
        self._result = result
        self._busy = False
        self._installing = False
        self.stateChanged.emit()

    @Slot(str)
    def _failed(self, message: str) -> None:
        self._busy = False
        self._installing = False
        self._error_message = message
        self._result["status"] = "Setup failed"
        self._result["message"] = "KoeScribe could not configure CUDA."
        self.stateChanged.emit()

    @Slot()
    def _worker_finished(self) -> None:
        if self._worker:
            self._worker.deleteLater()
            self._worker = None
