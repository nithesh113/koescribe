from __future__ import annotations

import tempfile
import time
import wave
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtMultimedia import QAudioDevice, QAudioFormat, QAudioSource, QMediaDevices


class AudioRecordingService(QObject):
    """Record one privacy-safe temporary PCM WAV file at a time."""

    recordingStopped = Signal(str)
    errorOccurred = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._audio_source: QAudioSource | None = None
        self._audio_device = None
        self._wave_file: wave.Wave_write | None = None
        self._temporary_path: Path | None = None
        self._recording = False
        self._temporary_directory = Path(tempfile.gettempdir()) / "koescribe"
        self._temporary_directory.mkdir(parents=True, exist_ok=True)
        self.cleanup_abandoned_recordings()

    @property
    def recording(self) -> bool:
        return self._recording

    @property
    def temporary_path(self) -> Path | None:
        return self._temporary_path

    def start(self, device_id: str = "") -> Path:
        if self._recording:
            raise RuntimeError("A recording is already in progress.")

        self.discard()
        device = self._find_device(device_id)
        if device is None:
            raise RuntimeError("No microphone is available.")

        audio_format = self._recording_format(device)
        with tempfile.NamedTemporaryFile(
            prefix="recording-",
            suffix=".wav",
            dir=self._temporary_directory,
            delete=False,
        ) as temporary_file:
            self._temporary_path = Path(temporary_file.name)

        try:
            # This writer intentionally remains open during asynchronous capture.
            self._wave_file = wave.open(  # noqa: SIM115
                str(self._temporary_path), "wb"
            )
            self._wave_file.setnchannels(audio_format.channelCount())
            self._wave_file.setsampwidth(2)
            self._wave_file.setframerate(audio_format.sampleRate())

            self._audio_source = QAudioSource(device, audio_format, self)
            self._audio_device = self._audio_source.start()
            if self._audio_device is None:
                raise RuntimeError("Qt could not open the selected microphone.")

            self._audio_device.readyRead.connect(self._read_available_audio)
            self._recording = True
            return self._temporary_path
        except Exception:
            self._close_audio_objects()
            self.discard()
            raise

    def stop(self) -> Path:
        if not self._recording or self._temporary_path is None:
            raise RuntimeError("No recording is in progress.")

        self._read_available_audio()
        completed_path = self._temporary_path
        self._close_audio_objects()

        if not completed_path.is_file() or completed_path.stat().st_size <= 44:
            self.discard()
            raise RuntimeError("The microphone did not provide any audio data.")

        self.recordingStopped.emit(str(completed_path))
        return completed_path

    def cancel(self) -> None:
        self._close_audio_objects()
        self.discard()

    def discard(self) -> None:
        path = self._temporary_path
        self._temporary_path = None
        if path is not None:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass

    def cleanup_abandoned_recordings(self, maximum_age_hours: int = 24) -> None:
        cutoff = time.time() - (maximum_age_hours * 60 * 60)
        for path in self._temporary_directory.glob("recording-*.wav"):
            try:
                if path.is_file() and path.stat().st_mtime < cutoff:
                    path.unlink()
            except OSError:
                continue

    def _read_available_audio(self) -> None:
        if self._audio_device is None or self._wave_file is None:
            return

        data = bytes(self._audio_device.readAll())
        if data:
            self._wave_file.writeframesraw(data)

    def _close_audio_objects(self) -> None:
        self._recording = False

        if self._audio_source is not None:
            self._audio_source.stop()
            self._audio_source.deleteLater()
            self._audio_source = None

        self._audio_device = None

        if self._wave_file is not None:
            self._wave_file.close()
            self._wave_file = None

    def _find_device(self, device_id: str) -> QAudioDevice | None:
        devices = list(QMediaDevices.audioInputs())
        if not devices:
            return None

        normalized_id = device_id.casefold()
        if normalized_id:
            for device in devices:
                if self._device_id(device).casefold() == normalized_id:
                    return device

        default_device = QMediaDevices.defaultAudioInput()
        if not default_device.isNull():
            return default_device
        return devices[0]

    def _device_id(self, device: QAudioDevice) -> str:
        return bytes(device.id()).hex()

    def _recording_format(self, device: QAudioDevice) -> QAudioFormat:
        requested = QAudioFormat()
        requested.setSampleRate(16_000)
        requested.setChannelCount(1)
        requested.setSampleFormat(QAudioFormat.SampleFormat.Int16)

        if device.isFormatSupported(requested):
            return requested

        preferred = device.preferredFormat()
        if preferred.sampleFormat() != QAudioFormat.SampleFormat.Int16:
            raise RuntimeError(
                "The selected microphone does not expose a supported 16-bit PCM format."
            )
        return preferred
