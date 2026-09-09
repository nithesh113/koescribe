from __future__ import annotations

from typing import Any

from PySide6.QtMultimedia import QAudioDevice, QMediaDevices


class MicrophoneService:
    """Discover audio-input devices using Qt Multimedia."""

    def get_microphones(self) -> list[dict[str, Any]]:
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

        return microphones

    def get_default_microphone_id(self) -> str:
        default_device = QMediaDevices.defaultAudioInput()
        return self._device_id(default_device)

    def find_microphone(
        self,
        device_id: str,
    ) -> QAudioDevice | None:
        for device in QMediaDevices.audioInputs():
            if self._device_id(device) == device_id:
                return device

        return None

    def has_microphone(self) -> bool:
        return bool(QMediaDevices.audioInputs())

    def _device_id(self, device: QAudioDevice) -> str:
        return bytes(device.id()).hex()