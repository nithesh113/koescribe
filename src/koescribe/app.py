from __future__ import annotations

import sys
from pathlib import Path

from koescribe.controllers.cuda_controller import CudaController
from koescribe.controllers.microphone_controller import MicrophoneController
from koescribe.controllers.setup_controller import SetupController
from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine


def main() -> int:
    app = QGuiApplication(sys.argv)
    app.setApplicationName("KoeScribe")
    app.setApplicationDisplayName("KoeScribe")
    app.setOrganizationName("KoeScribe")
    # app.setDesktopFileName("com.koescribe.KoeScribe")

    package_directory = Path(__file__).resolve().parent
    icon_file = package_directory / "qml" / "assets" / "koescribe-icon.png"
    if icon_file.is_file():
        app.setWindowIcon(QIcon(str(icon_file)))

    engine = QQmlApplicationEngine()

    setup_controller = SetupController()
    microphone_controller = MicrophoneController()
    cuda_controller = CudaController()

    context = engine.rootContext()
    context.setContextProperty("setupController", setup_controller)
    context.setContextProperty(
        "microphoneController",
        microphone_controller,
    )
    context.setContextProperty("cudaController", cuda_controller)

    qml_file = package_directory / "qml" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))

    if not engine.rootObjects():
        return 1

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
