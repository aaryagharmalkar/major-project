"""ComfyUI REST API client for queueing and retrieving generated videos."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx


class ComfyUIError(RuntimeError):
    """Raised when ComfyUI returns an error or becomes unreachable."""


@dataclass(frozen=True)
class GeneratedOutput:
    filename: str
    subfolder: str
    file_type: str


class ComfyUIClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8188", *, timeout: float = 60.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client_id = str(uuid.uuid4())

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def check_server(self) -> None:
        try:
            response = httpx.get(self._url("/system_stats"), timeout=5.0)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ComfyUIError(
                f"ComfyUI is not reachable at {self.base_url}. "
                "Start it with scripts/start_comfyui.ps1"
            ) from exc

    def queue_prompt(self, prompt: dict[str, Any]) -> str:
        payload = {"prompt": prompt, "client_id": self.client_id}
        response = httpx.post(self._url("/prompt"), json=payload, timeout=self.timeout)
        if response.status_code >= 400:
            raise ComfyUIError(f"ComfyUI rejected prompt: {response.status_code} {response.text}")
        data = response.json()
        prompt_id = data.get("prompt_id")
        if not prompt_id:
            node_errors = data.get("node_errors")
            raise ComfyUIError(f"ComfyUI did not return prompt_id. node_errors={node_errors}")
        return str(prompt_id)

    def get_history(self, prompt_id: str) -> dict[str, Any] | None:
        response = httpx.get(self._url(f"/history/{prompt_id}"), timeout=self.timeout)
        response.raise_for_status()
        history = response.json()
        return history.get(prompt_id)

    def wait_for_completion(
        self,
        prompt_id: str,
        *,
        poll_interval: float = 2.0,
        timeout_seconds: float = 900.0,
    ) -> dict[str, Any]:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            history = self.get_history(prompt_id)
            if history:
                status = history.get("status") or {}
                if status.get("status_str") == "error":
                    raise ComfyUIError(self._format_execution_error(history))
                if history.get("outputs"):
                    return history
            time.sleep(poll_interval)
        raise ComfyUIError(f"Timed out waiting for ComfyUI prompt {prompt_id}")

    @staticmethod
    def _format_execution_error(history: dict[str, Any]) -> str:
        messages = history.get("status", {}).get("messages") or []
        for message in reversed(messages):
            if len(message) >= 2 and message[0] == "execution_error":
                details = message[1]
                node_type = details.get("node_type", "unknown")
                node_id = details.get("node_id", "?")
                exc = details.get("exception_message", "Unknown ComfyUI execution error")
                return f"ComfyUI node {node_id} ({node_type}) failed: {exc.strip()}"
        return "ComfyUI execution failed with an unknown error"

    def extract_outputs(self, history: dict[str, Any]) -> list[GeneratedOutput]:
        outputs: list[GeneratedOutput] = []
        for node_output in history.get("outputs", {}).values():
            for key in ("images", "gifs", "videos"):
                for item in node_output.get(key, []):
                    outputs.append(
                        GeneratedOutput(
                            filename=item["filename"],
                            subfolder=item.get("subfolder", ""),
                            file_type=item.get("type", "output"),
                        )
                    )
        return outputs

    def download_output(self, output: GeneratedOutput) -> bytes:
        params = urlencode(
            {
                "filename": output.filename,
                "subfolder": output.subfolder,
                "type": output.file_type,
            }
        )
        response = httpx.get(self._url(f"/view?{params}"), timeout=self.timeout)
        response.raise_for_status()
        return response.content

    def save_first_output(
        self,
        history: dict[str, Any],
        destination: Path,
    ) -> GeneratedOutput:
        outputs = self.extract_outputs(history)
        if not outputs:
            status = history.get("status", {})
            messages = status.get("messages", [])
            raise ComfyUIError(f"No output files in ComfyUI history. status={status} messages={messages}")
        output = outputs[0]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(self.download_output(output))
        return output

    def upload_image(
        self,
        image_path: Path,
        *,
        subfolder: str = "",
        overwrite: bool = True,
    ) -> str:
        """Upload a local image to ComfyUI input folder. Returns the filename for LoadImage."""
        with image_path.open("rb") as handle:
            response = httpx.post(
                self._url("/upload/image"),
                files={"image": (image_path.name, handle, "application/octet-stream")},
                data={
                    "subfolder": subfolder,
                    "type": "input",
                    "overwrite": "true" if overwrite else "false",
                },
                timeout=self.timeout,
            )
        if response.status_code >= 400:
            raise ComfyUIError(f"ComfyUI image upload failed: {response.status_code} {response.text}")
        data = response.json()
        name = data.get("name")
        if not name:
            raise ComfyUIError(f"ComfyUI upload did not return image name: {data}")
        return str(name)
