from __future__ import annotations

import math
import struct
from typing import Any

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot
from PySide6.QtMultimedia import (
    QAudioFormat,
    QAudioSource,
    QMediaDevices,
)


class MicrophoneController(QObject):
    microphonesChanged = Signal()
    selectedMicrophoneChanged = Signal()
    testStateChanged = Signal()
    inputLevelChanged = Signal()
    statusChanged = Signal()

    def __init__(self) -> None:
        super().__init__()

        self._media_devices = QMediaDevices()

        self._microphones: list[dict[str, Any]] = []
        self._selected_microphone_id = ""

        self._testing = False
        self._input_level = 0.0
        self._status = "Ready to test"

        self._audio_source: QAudioSource | None = None
        self._audio_stream = None
        self._audio_format = QAudioFormat()

        self._test_timer = QTimer(self)
        self._test_timer.setSingleShot(True)
        self._test_timer.timeout.connect(self.stopTest)

        self._media_devices.audioInputsChanged.connect(
            self.refreshMicrophones
        )

        self.refreshMicrophones()

    @Property(
        "QVariantList",
        notify=microphonesChanged,
    )
    def microphones(self) -> list[dict[str, Any]]:
        return self._microphones

    @Property(
        str,
        notify=selectedMicrophoneChanged,
    )
    def selectedMicrophoneId(self) -> str:
        return self._selected_microphone_id

    @Property(
        "QVariantMap",
        notify=selectedMicrophoneChanged,
    )
    def selectedMicrophone(self) -> dict[str, Any]:
        for microphone in self._microphones:
            if (
                microphone["device_id"]
                == self._selected_microphone_id
            ):
                return microphone

        return {}

    @Property(bool, notify=testStateChanged)
    def testing(self) -> bool:
        return self._testing

    @Property(float, notify=inputLevelChanged)
    def inputLevel(self) -> float:
        return self._input_level

    @Property(str, notify=statusChanged)
    def status(self) -> str:
        return self._status

    @Property(bool, notify=microphonesChanged)
    def hasMicrophone(self) -> bool:
        return bool(self._microphones)

    @Slot()
    def refreshMicrophones(self) -> None:
        devices = QMediaDevices.audioInputs()
        default_device = QMediaDevices.defaultAudioInput()
        default_id = self._device_id(default_device)

        microphones: list[dict[str, Any]] = []

        for device in devices:
            device_id = self._device_id(device)

            microphones.append(
                {
                    "device_id": device_id,
                    "name": device.description(),
                    "is_default": device_id == default_id,
                    "minimum_sample_rate": (
                        device.minimumSampleRate()
                    ),
                    "maximum_sample_rate": (
                        device.maximumSampleRate()
                    ),
                    "minimum_channels": (
                        device.minimumChannelCount()
                    ),
                    "maximum_channels": (
                        device.maximumChannelCount()
                    ),
                }
            )

        self._microphones = microphones

        available_ids = {
            microphone["device_id"]
            for microphone in microphones
        }

        if self._selected_microphone_id not in available_ids:
            self._selected_microphone_id = default_id

            if (
                not self._selected_microphone_id
                and microphones
            ):
                self._selected_microphone_id = str(
                    microphones[0]["device_id"]
                )

            self.selectedMicrophoneChanged.emit()

        if not microphones:
            self._set_status("No microphone detected")
        elif not self._testing:
            self._set_status("Ready to test")

        self.microphonesChanged.emit()

    @Slot(str)
    def selectMicrophone(self, device_id: str) -> None:
        if self._testing:
            self.stopTest()

        available_ids = {
            microphone["device_id"]
            for microphone in self._microphones
        }

        if device_id not in available_ids:
            self._set_status(
                "The selected microphone is unavailable"
            )
            return

        self._selected_microphone_id = device_id

        self.selectedMicrophoneChanged.emit()
        self._set_status("Ready to test")

    @Slot()
    def startTest(self) -> None:
        if self._testing:
            return

        device = self._find_selected_device()

        if device is None:
            self._set_status("Select a microphone first")
            return

        requested_format = QAudioFormat()
        requested_format.setSampleRate(16000)
        requested_format.setChannelCount(1)
        requested_format.setSampleFormat(
            QAudioFormat.SampleFormat.Int16
        )

        if device.isFormatSupported(requested_format):
            self._audio_format = requested_format
        else:
            self._audio_format = device.preferredFormat()

        self._audio_source = QAudioSource(
            device,
            self._audio_format,
            self,
        )

        self._audio_source.setBufferSize(4096)

        self._audio_stream = self._audio_source.start()

        if self._audio_stream is None:
            self._audio_source.deleteLater()
            self._audio_source = None

            self._set_status(
                "Could not access the selected microphone"
            )
            return

        self._audio_stream.readyRead.connect(
            self._read_audio_data
        )

        self._testing = True
        self._input_level = 0.0

        self.testStateChanged.emit()
        self.inputLevelChanged.emit()

        self._set_status("Listening — speak now")

        self._test_timer.start(5000)

    @Slot()
    def stopTest(self) -> None:
        self._test_timer.stop()

        if self._audio_stream is not None:
            try:
                self._audio_stream.readyRead.disconnect(
                    self._read_audio_data
                )
            except RuntimeError:
                pass

            self._audio_stream = None

        if self._audio_source is not None:
            self._audio_source.stop()
            self._audio_source.deleteLater()
            self._audio_source = None

        was_testing = self._testing

        self._testing = False
        self._input_level = 0.0

        if was_testing:
            self.testStateChanged.emit()

        self.inputLevelChanged.emit()
        self._set_status("Microphone test completed")

    @Slot()
    def _read_audio_data(self) -> None:
        if self._audio_stream is None:
            return

        raw_data = bytes(
            self._audio_stream.readAll()
        )

        if not raw_data:
            return

        level = self._calculate_level(
            raw_data,
            self._audio_format.sampleFormat(),
        )

        if abs(level - self._input_level) < 0.01:
            return

        self._input_level = level
        self.inputLevelChanged.emit()

    def _calculate_level(
        self,
        raw_data: bytes,
        sample_format: QAudioFormat.SampleFormat,
    ) -> float:
        samples: list[float]

        if sample_format == QAudioFormat.SampleFormat.Int16:
            usable_length = len(raw_data) - len(raw_data) % 2

            samples = [
                sample[0] / 32768.0
                for sample in struct.iter_unpack(
                    "<h",
                    raw_data[:usable_length],
                )
            ]

        elif sample_format == QAudioFormat.SampleFormat.Int32:
            usable_length = len(raw_data) - len(raw_data) % 4

            samples = [
                sample[0] / 2147483648.0
                for sample in struct.iter_unpack(
                    "<i",
                    raw_data[:usable_length],
                )
            ]

        elif sample_format == QAudioFormat.SampleFormat.Float:
            usable_length = len(raw_data) - len(raw_data) % 4

            samples = [
                sample[0]
                for sample in struct.iter_unpack(
                    "<f",
                    raw_data[:usable_length],
                )
            ]

        elif sample_format == QAudioFormat.SampleFormat.UInt8:
            samples = [
                (sample - 128) / 128.0
                for sample in raw_data
            ]

        else:
            return 0.0

        if not samples:
            return 0.0

        square_total = sum(
            sample * sample
            for sample in samples
        )

        rms = math.sqrt(
            square_total / len(samples)
        )

        amplified_level = rms * 4.0

        return max(
            0.0,
            min(1.0, amplified_level),
        )

    def _find_selected_device(self):
        for device in QMediaDevices.audioInputs():
            if (
                self._device_id(device)
                == self._selected_microphone_id
            ):
                return device

        return None

    def _device_id(self, device) -> str:
        return bytes(device.id()).hex()

    def _set_status(self, status: str) -> None:
        if status == self._status:
            return

        self._status = status
        self.statusChanged.emit()