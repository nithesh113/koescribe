from __future__ import annotations

import ctypes
import ctypes.util
import importlib.util
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

CUDA_PACKAGES = (
    "nvidia-cublas-cu12",
    "nvidia-cudnn-cu12==9.*",
)


@dataclass
class CudaStatus:
    ready: bool
    gpu_detected: bool
    cublas_detected: bool
    cudnn_detected: bool
    device_count: int
    status: str
    message: str
    missing: list[str]
    install_supported: bool
    install_command: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CudaService:
    """Detect and install KoeScribe's app-local CUDA runtime libraries."""

    def detect(self) -> CudaStatus:
        gpu_detected = self._nvidia_gpu_available()
        cublas_paths = self._candidate_libraries("cublas", ("libcublasLt.so.12", "libcublas.so.12"))
        cudnn_paths = self._candidate_libraries("cudnn", ("libcudnn.so.9",))
        cublas_detected = bool(cublas_paths)
        cudnn_detected = bool(cudnn_paths)
        missing: list[str] = []

        if not cublas_detected:
            missing.append("cuBLAS 12")
        if not cudnn_detected:
            missing.append("cuDNN 9")

        install_supported = platform.system() == "Linux"
        install_command = (
            'uv pip install nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*"'
            if install_supported
            else "Install CUDA 12 cuBLAS and cuDNN 9 manually."
        )

        if not gpu_detected:
            return CudaStatus(
                ready=False,
                gpu_detected=False,
                cublas_detected=cublas_detected,
                cudnn_detected=cudnn_detected,
                device_count=0,
                status="CPU mode",
                message=(
                    "No working NVIDIA GPU was detected. KoeScribe can use CPU transcription."
                ),
                missing=missing,
                install_supported=False,
                install_command=install_command,
            )

        if missing:
            return CudaStatus(
                ready=False,
                gpu_detected=True,
                cublas_detected=cublas_detected,
                cudnn_detected=cudnn_detected,
                device_count=0,
                status="Setup needed",
                message=f"Missing: {', '.join(missing)}",
                missing=missing,
                install_supported=install_supported,
                install_command=install_command,
            )

        try:
            self.prepare_runtime()
            import ctranslate2

            device_count = int(ctranslate2.get_cuda_device_count())
            if device_count < 1:
                raise RuntimeError("CTranslate2 found no CUDA devices.")
        except Exception as error:  # noqa: BLE001 - include loader errors in status
            return CudaStatus(
                ready=False,
                gpu_detected=True,
                cublas_detected=True,
                cudnn_detected=True,
                device_count=0,
                status="Verification failed",
                message=f"CUDA libraries were found, but verification failed: {error}",
                missing=[],
                install_supported=install_supported,
                install_command=install_command,
            )

        return CudaStatus(
            ready=True,
            gpu_detected=True,
            cublas_detected=True,
            cudnn_detected=True,
            device_count=device_count,
            status="Ready",
            message=f"CUDA acceleration is ready on {device_count} NVIDIA GPU.",
            missing=[],
            install_supported=install_supported,
            install_command=install_command,
        )

    def install(self) -> CudaStatus:
        if platform.system() != "Linux":
            raise RuntimeError("Automatic CUDA runtime installation is currently Linux-only.")

        command = self._installer_command()
        result = subprocess.run(
            [*command, *CUDA_PACKAGES],
            capture_output=True,
            text=True,
            timeout=900,
            check=False,
        )
        if result.returncode != 0:
            details = result.stderr.strip() or result.stdout.strip()
            raise RuntimeError(details or "The CUDA package installation failed.")

        importlib.invalidate_caches()
        status = self.detect()
        if not status.ready:
            raise RuntimeError(status.message)
        return status

    def prepare_runtime(self) -> list[str]:
        """Load app-local CUDA libraries globally before CTranslate2 uses them."""
        loaded: list[str] = []
        ordered_libraries = (
            ("cublas", "libcublasLt.so.12"),
            ("cublas", "libcublas.so.12"),
            ("cudnn", "libcudnn.so.9"),
        )

        for package_name, library_name in ordered_libraries:
            paths = self._candidate_libraries(package_name, (library_name,))
            target = str(paths[0]) if paths else library_name
            ctypes.CDLL(target, mode=ctypes.RTLD_GLOBAL)
            loaded.append(target)

        return loaded

    def _installer_command(self) -> list[str]:
        uv = shutil.which("uv")
        if uv:
            return [uv, "pip", "install", "--python", sys.executable]

        try:
            pip_check = subprocess.run(
                [sys.executable, "-m", "pip", "--version"],
                capture_output=True,
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            pip_check = None

        if pip_check and pip_check.returncode == 0:
            return [sys.executable, "-m", "pip", "install"]

        raise RuntimeError(
            "Neither uv nor pip is available. Run: "
            'uv pip install nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*"'
        )

    def _candidate_libraries(
        self,
        package_name: str,
        library_names: tuple[str, ...],
    ) -> list[Path]:
        found: list[Path] = []
        package_directory = self._nvidia_library_directory(package_name)

        if package_directory:
            for library_name in library_names:
                candidate = package_directory / library_name
                if candidate.is_file():
                    found.append(candidate)

        for directory in self._system_library_directories():
            for library_name in library_names:
                candidate = directory / library_name
                if candidate.is_file() and candidate not in found:
                    found.append(candidate)

        for lookup_name in library_names:
            resolved = ctypes.util.find_library(lookup_name)
            if resolved:
                candidate = Path(resolved)
                if candidate not in found:
                    found.append(candidate)

        return found

    def _nvidia_library_directory(self, package_name: str) -> Path | None:
        try:
            spec = importlib.util.find_spec(f"nvidia.{package_name}")
        except (ImportError, ModuleNotFoundError, ValueError):
            return None
        if spec is None or not spec.submodule_search_locations:
            return None

        package_directory = Path(next(iter(spec.submodule_search_locations)))
        library_directory = package_directory / "lib"
        return library_directory if library_directory.is_dir() else None

    def _system_library_directories(self) -> tuple[Path, ...]:
        directories = [
            Path("/usr/lib64"),
            Path("/usr/lib"),
            Path("/usr/local/cuda/lib64"),
            Path("/usr/local/lib64"),
        ]
        for entry in os.environ.get("LD_LIBRARY_PATH", "").split(":"):
            if entry:
                directories.append(Path(entry))
        return tuple(dict.fromkeys(directories))

    def _nvidia_gpu_available(self) -> bool:
        executable = shutil.which("nvidia-smi")
        if executable is None:
            return False
        try:
            result = subprocess.run(
                [executable, "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return False
        return result.returncode == 0 and bool(result.stdout.strip())
