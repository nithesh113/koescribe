from __future__ import annotations

import ctypes.util
import os
import platform
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from koescribe.services.cuda_service import CudaService


@dataclass
class CheckResult:
    key: str
    title: str
    description: str
    status: str
    ready: bool
    required: bool = True
    action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SystemInformation:
    operating_system: str
    operating_system_version: str
    desktop_environment: str
    session_type: str
    architecture: str
    checks: list[CheckResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "operating_system": self.operating_system,
            "operating_system_version": self.operating_system_version,
            "desktop_environment": self.desktop_environment,
            "session_type": self.session_type,
            "architecture": self.architecture,
            "checks": [check.to_dict() for check in self.checks],
        }


class SystemService:
    """Detect system requirements without changing the user's computer."""

    def detect(self) -> SystemInformation:
        operating_system = platform.system()

        if operating_system == "Linux":
            return self._detect_linux()
        if operating_system == "Windows":
            return self._detect_windows()
        return self._detect_unsupported(operating_system)

    def _detect_linux(self) -> SystemInformation:
        distribution_name, distribution_version = self._read_linux_release()
        desktop = (
            os.environ.get("XDG_CURRENT_DESKTOP")
            or os.environ.get("DESKTOP_SESSION")
            or "Unknown desktop"
        )
        session = os.environ.get("XDG_SESSION_TYPE", "Unknown session")

        return SystemInformation(
            operating_system="Linux",
            operating_system_version=f"{distribution_name} {distribution_version}".strip(),
            desktop_environment=desktop,
            session_type=session,
            architecture=platform.machine(),
            checks=[
                self._check_linux_distribution(distribution_name, distribution_version),
                self._check_linux_session(desktop, session),
                self._check_nvidia_gpu(),
                self._check_cuda_runtime(),
                self._check_linux_microphone(),
            ],
        )

    def _detect_windows(self) -> SystemInformation:
        return SystemInformation(
            operating_system="Windows",
            operating_system_version=platform.version(),
            desktop_environment="Windows desktop",
            session_type="Windows",
            architecture=platform.machine(),
            checks=[
                CheckResult(
                    key="operating_system",
                    title="Operating system",
                    description=f"Windows {platform.release()}",
                    status="Ready",
                    ready=True,
                ),
                CheckResult(
                    key="desktop_session",
                    title="Desktop session",
                    description="Windows desktop",
                    status="Ready",
                    ready=True,
                ),
                self._check_nvidia_gpu(),
                self._check_cuda_runtime(),
                self._check_windows_microphone(),
            ],
        )

    def _detect_unsupported(self, operating_system: str) -> SystemInformation:
        return SystemInformation(
            operating_system=operating_system,
            operating_system_version=platform.version(),
            desktop_environment="Unknown",
            session_type="Unknown",
            architecture=platform.machine(),
            checks=[
                CheckResult(
                    key="operating_system",
                    title="Operating system",
                    description=f"{operating_system} is not supported yet.",
                    status="Unsupported",
                    ready=False,
                    action="KoeScribe currently supports Linux and Windows.",
                )
            ],
        )

    def _read_linux_release(self) -> tuple[str, str]:
        release_file = Path("/etc/os-release")
        if not release_file.exists():
            return "Linux", platform.release()

        values: dict[str, str] = {}
        try:
            for line in release_file.read_text(encoding="utf-8").splitlines():
                if "=" in line:
                    key, value = line.split("=", 1)
                    values[key] = value.strip().strip('"')
        except OSError:
            return "Linux", platform.release()

        return (
            values.get("NAME", "Linux"),
            values.get("VERSION_ID", platform.release()),
        )

    def _check_linux_distribution(self, name: str, version: str) -> CheckResult:
        supported_names = {
            "fedora linux",
            "fedora",
            "ubuntu",
            "debian gnu/linux",
            "debian",
            "linux mint",
            "pop!_os",
            "arch linux",
        }
        ready = name.casefold() in supported_names

        return CheckResult(
            key="operating_system",
            title="Operating system",
            description=f"{name} {version}",
            status="Ready" if ready else "Limited support",
            ready=ready,
            action="" if ready else "This Linux distribution has not been tested yet.",
        )

    def _check_linux_session(self, desktop: str, session: str) -> CheckResult:
        session_lower = session.casefold()
        supported = session_lower in {"wayland", "x11"}

        if session_lower == "wayland":
            description = f"{desktop} on Wayland detected."
        elif session_lower == "x11":
            description = f"{desktop} on X11 detected."
        else:
            description = f"{desktop} using {session}."

        return CheckResult(
            key="desktop_session",
            title="Desktop session",
            description=description,
            status="Ready" if supported else "Unknown",
            ready=supported,
            action="" if supported else "KoeScribe could not identify the display session.",
        )

    def _check_nvidia_gpu(self) -> CheckResult:
        executable = shutil.which("nvidia-smi")
        if executable is None:
            return CheckResult(
                key="nvidia_gpu",
                title="NVIDIA GPU",
                description="NVIDIA driver was not detected.",
                status="Not found",
                ready=False,
                required=False,
                action="Install an NVIDIA driver or use CPU transcription.",
            )

        result = self._run_command(
            [
                executable,
                "--query-gpu=name,memory.total,driver_version",
                "--format=csv,noheader",
            ]
        )
        if not result:
            return CheckResult(
                key="nvidia_gpu",
                title="NVIDIA GPU",
                description="nvidia-smi could not access the GPU.",
                status="Check driver",
                ready=False,
                required=False,
                action="Verify that the NVIDIA driver is loaded.",
            )

        return CheckResult(
            key="nvidia_gpu",
            title="NVIDIA GPU",
            description=result.splitlines()[0].strip(),
            status="Ready",
            ready=True,
            required=False,
        )

    def _check_cuda_runtime(self) -> CheckResult:
        status = CudaService().detect()
        return CheckResult(
            key="cuda_runtime",
            title="CUDA acceleration",
            description=status.message,
            status=status.status,
            ready=status.ready,
            required=False,
            action=(
                "KoeScribe can install the missing runtime libraries."
                if status.install_supported and not status.ready
                else ""
            ),
        )

    def _check_linux_microphone(self) -> CheckResult:
        wpctl = shutil.which("wpctl")
        if wpctl:
            result = self._run_command([wpctl, "status"])
            if result and "Sources:" in result:
                return CheckResult(
                    key="microphone",
                    title="Microphone",
                    description="An audio input is available through PipeWire.",
                    status="Ready",
                    ready=True,
                )

        pactl = shutil.which("pactl")
        if pactl:
            result = self._run_command([pactl, "list", "short", "sources"])
            if result:
                return CheckResult(
                    key="microphone",
                    title="Microphone",
                    description="An audio input device was detected.",
                    status="Ready",
                    ready=True,
                )

        return CheckResult(
            key="microphone",
            title="Microphone",
            description="No audio input device was detected.",
            status="Not found",
            ready=False,
            action="Connect a microphone and check its permissions.",
        )

    def _check_windows_microphone(self) -> CheckResult:
        powershell = shutil.which("powershell") or shutil.which("pwsh")
        if powershell is None:
            return CheckResult(
                key="microphone",
                title="Microphone",
                description="The microphone check could not run.",
                status="Check manually",
                ready=False,
                action="Confirm microphone access in Windows Settings.",
            )

        result = self._run_command(
            [
                powershell,
                "-NoProfile",
                "-Command",
                (
                    "Get-CimInstance Win32_SoundDevice "
                    "| Where-Object {$_.Status -eq 'OK'} "
                    "| Select-Object -ExpandProperty Name"
                ),
            ]
        )
        if result:
            return CheckResult(
                key="microphone",
                title="Audio device",
                description=result.splitlines()[0].strip(),
                status="Ready",
                ready=True,
            )

        return CheckResult(
            key="microphone",
            title="Microphone",
            description="No enabled audio device was detected.",
            status="Not found",
            ready=False,
            action="Enable microphone access in Windows Settings.",
        )

    def _library_exists(self, names: list[str]) -> bool:
        for name in names:
            if ctypes.util.find_library(name):
                return True
            if (
                platform.system() == "Linux"
                and name.startswith("lib")
                and self._find_linux_library(name)
            ):
                return True
        return False

    def _find_linux_library(self, library_name: str) -> bool:
        search_directories = [
            Path("/usr/lib64"),
            Path("/usr/lib"),
            Path("/usr/local/cuda/lib64"),
            Path("/usr/local/lib64"),
        ]
        return any(
            any(directory.glob(f"{library_name}*"))
            for directory in search_directories
            if directory.exists()
        )

    def _run_command(self, command: list[str], timeout: int = 5) -> str | None:
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return None

        if result.returncode != 0:
            return None
        return result.stdout.strip()
