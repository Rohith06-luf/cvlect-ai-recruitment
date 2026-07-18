from __future__ import annotations

from typing import Any

try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None

from app.core.config import settings


class NIMClient:
    def __init__(
        self,
        api_url: str | None = None,
        api_key: str | None = None,
        model_name: str | None = None,
        timeout: int = 30,
    ) -> None:
        self.api_url = api_url or settings.NIM_API_URL
        self.api_key = api_key or settings.NIM_API_KEY
        self.model_name = model_name or settings.NIM_MODEL_NAME
        self.timeout = timeout

    def is_configured(self) -> bool:
        return bool(self.api_url and self.api_key and httpx is not None)

    def generate(self, prompt: str) -> str | None:
        if not self.is_configured():
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {"input": prompt}
        if self.model_name:
            payload["model"] = self.model_name

        try:
            response = httpx.post(self.api_url, json=payload, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            response_data = response.json()
        except Exception as exc:
            raise RuntimeError(f"NIM request failed: {exc}") from exc

        return self._parse_response(response_data)

    def _parse_response(self, data: Any) -> str | None:
        if not isinstance(data, dict):
            return None

        if "output" in data:
            output = data["output"]
            if isinstance(output, str):
                return output
            if isinstance(output, dict):
                return output.get("text") or output.get("content")

        if "outputs" in data and isinstance(data["outputs"], list) and data["outputs"]:
            first = data["outputs"][0]
            if isinstance(first, dict):
                if "content" in first:
                    content = first["content"]
                    if isinstance(content, str):
                        return content
                    if isinstance(content, list) and content:
                        first_content = content[0]
                        if isinstance(first_content, dict):
                            return first_content.get("text") or first_content.get("content")
                return first.get("text") or first.get("content") or first.get("output")

        if "choices" in data and isinstance(data["choices"], list) and data["choices"]:
            choice = data["choices"][0]
            if isinstance(choice, dict):
                return choice.get("text") or choice.get("message", {}).get("content") if isinstance(choice.get("message"), dict) else None

        if "data" in data and isinstance(data["data"], list) and data["data"]:
            first = data["data"][0]
            if isinstance(first, dict):
                return first.get("text") or first.get("output")

        if "generated_text" in data and isinstance(data["generated_text"], str):
            return data["generated_text"]

        return None
