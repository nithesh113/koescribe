from __future__ import annotations

import platform
from dataclasses import asdict, dataclass
from typing import Any

import httpx


DEFAULT_LM_STUDIO_URL = "http://127.0.0.1:1234/v1"


@dataclass
class LMStudioResult:
    connected: bool
    base_url: str
    status: str
    message: str
    models: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class LMStudioService:
    """Check and communicate with the LM Studio local server."""

    def __init__(
        self,
        base_url: str = DEFAULT_LM_STUDIO_URL,
        timeout: float = 5.0,
    ) -> None:
        self.base_url = self.normalize_base_url(base_url)
        self.timeout = timeout

    def check_connection(self) -> LMStudioResult:
        endpoint = f"{self.base_url}/models"

        try:
            response = httpx.get(
                endpoint,
                timeout=self.timeout,
            )

            response.raise_for_status()
            payload = response.json()

        except httpx.ConnectError:
            return LMStudioResult(
                connected=False,
                base_url=self.base_url,
                status="Not running",
                message=(
                    "KoeScribe could not connect to LM Studio. "
                    "Start the Local Server in LM Studio."
                ),
                models=[],
            )

        except httpx.TimeoutException:
            return LMStudioResult(
                connected=False,
                base_url=self.base_url,
                status="Timed out",
                message=(
                    "LM Studio did not respond before the "
                    "connection timed out."
                ),
                models=[],
            )

        except httpx.HTTPStatusError as error:
            return LMStudioResult(
                connected=False,
                base_url=self.base_url,
                status="Server error",
                message=(
                    "LM Studio returned HTTP status "
                    f"{error.response.status_code}."
                ),
                models=[],
            )

        except (ValueError, TypeError):
            return LMStudioResult(
                connected=False,
                base_url=self.base_url,
                status="Invalid response",
                message=(
                    "The server responded, but it did not return "
                    "a valid LM Studio model list."
                ),
                models=[],
            )

        models = self._parse_models(payload)

        if not models:
            return LMStudioResult(
                connected=True,
                base_url=self.base_url,
                status="No model loaded",
                message=(
                    "LM Studio is running, but no model is available. "
                    "Load an instruct model in LM Studio."
                ),
                models=[],
            )

        return LMStudioResult(
            connected=True,
            base_url=self.base_url,
            status="Connected",
            message=(
                f"LM Studio is ready with {len(models)} "
                f"available model{'s' if len(models) != 1 else ''}."
            ),
            models=models,
        )

    def get_setup_steps(self) -> list[str]:
        operating_system = platform.system()

        if operating_system == "Linux":
            return [
                "Open LM Studio on Linux.",
                "Download a small instruct model.",
                "Open the Developer tab.",
                "Load the downloaded model.",
                "Start the Local Server.",
                "Return to KoeScribe and test the connection.",
            ]

        if operating_system == "Windows":
            return [
                "Open LM Studio on Windows.",
                "Download a small instruct model.",
                "Open the Developer tab.",
                "Load the downloaded model.",
                "Start the Local Server.",
                "Return to KoeScribe and test the connection.",
            ]

        return [
            "Open LM Studio.",
            "Download and load an instruct model.",
            "Open the Developer tab.",
            "Start the Local Server.",
            "Return to KoeScribe and test the connection.",
        ]

    def normalize_base_url(self, base_url: str) -> str:
        normalized = base_url.strip().rstrip("/")

        if not normalized:
            return DEFAULT_LM_STUDIO_URL

        if normalized.endswith("/v1"):
            return normalized

        return f"{normalized}/v1"

    def _parse_models(
        self,
        payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        raw_models = payload.get("data", [])

        if not isinstance(raw_models, list):
            return []

        models: list[dict[str, Any]] = []

        for raw_model in raw_models:
            if not isinstance(raw_model, dict):
                continue

            model_id = raw_model.get("id")

            if not isinstance(model_id, str) or not model_id:
                continue

            model_id_lower = model_id.casefold()

            if (
                "embed" in model_id_lower
                or "embedding" in model_id_lower
            ):
                continue

            models.append(
                {
                    "model_id": model_id,
                    "name": model_id,
                    "owned_by": raw_model.get(
                        "owned_by",
                        "local",
                    ),
                }
            )

        return models