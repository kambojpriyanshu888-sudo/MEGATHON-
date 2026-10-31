"""Small Python client for BHASHINI's ULCA-style ASR, translation and TTS APIs.

Credentials are read from environment variables; never commit keys to GitHub.
"""
from __future__ import annotations

import base64
import os
from typing import Any

import requests


class BhashiniError(RuntimeError):
    """Raised when a BHASHINI request cannot be completed."""


class BhashiniClient:
    CONFIG_URL = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"
    DEFAULT_PIPELINE_ID = "64392f96daac500b55c543cd"
    DEFAULT_INFERENCE_URL = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"

    def __init__(
        self,
        user_id: str | None = None,
        api_key: str | None = None,
        pipeline_id: str | None = None,
        timeout: int = 60,
    ) -> None:
        self.user_id = (user_id or os.getenv("BHASHINI_USER_ID", "")).strip()
        self.api_key = (api_key or os.getenv("BHASHINI_API_KEY", "")).strip()
        self.pipeline_id = (pipeline_id or os.getenv("BHASHINI_PIPELINE_ID", self.DEFAULT_PIPELINE_ID)).strip()
        self.timeout = timeout

    @property
    def is_configured(self) -> bool:
        return bool(self.user_id and self.api_key)

    def _request_json(self, url: str, *, headers: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        except requests.RequestException as exc:
            raise BhashiniError(f"Could not connect to BHASHINI: {exc}") from exc
        if not response.ok:
            detail = response.text[:600]
            raise BhashiniError(f"BHASHINI returned HTTP {response.status_code}: {detail}")
        try:
            return response.json()
        except ValueError as exc:
            raise BhashiniError("BHASHINI returned a response that was not valid JSON.") from exc

    @staticmethod
    def _walk_dicts(node: Any):
        """Yield dictionaries at every level of a nested JSON response."""
        if isinstance(node, dict):
            yield node
            for value in node.values():
                yield from BhashiniClient._walk_dicts(value)
        elif isinstance(node, list):
            for value in node:
                yield from BhashiniClient._walk_dicts(value)

    def _pipeline_details(self, task_type: str, language: dict[str, str]) -> tuple[str, dict[str, str], str]:
        if not self.is_configured:
            raise BhashiniError(
                "BHASHINI is not configured. Add BHASHINI_USER_ID and BHASHINI_API_KEY to your .env file."
            )

        metadata = self._request_json(
            self.CONFIG_URL,
            headers={
                "userID": self.user_id,
                "ulcaApiKey": self.api_key,
                "Content-Type": "application/json",
            },
            payload={
                "pipelineId": self.pipeline_id,
                "taskType": [task_type],
                "config": {"language": language},
            },
        )

        # API response shapes can vary across pipeline/model versions. Look for the
        # service ID that matches the requested language pair, then use the first
        # service ID as a defensive fallback.
        candidates = []
        for item in self._walk_dicts(metadata):
            service_id = item.get("serviceId") or item.get("serviceID")
            if service_id:
                candidates.append(item)

        def language_matches(item: dict[str, Any]) -> bool:
            item_language = item.get("language")
            if not isinstance(item_language, dict):
                return False
            return all(item_language.get(key) == val for key, val in language.items())

        matching = next((item for item in candidates if language_matches(item)), None)
        chosen = matching or (candidates[0] if candidates else None)
        if not chosen:
            raise BhashiniError(
                f"No {task_type} model was returned for language setting {language}. Check your BHASHINI account and supported language pair."
            )
        service_id = str(chosen.get("serviceId") or chosen.get("serviceID"))

        endpoint_details = metadata.get("pipelineInferenceAPIEndPoint") or metadata.get("pipelineInferenceApiEndPoint") or {}
        if not isinstance(endpoint_details, dict):
            endpoint_details = {}
        callback_url = (
            endpoint_details.get("callbackURL")
            or endpoint_details.get("callbackUrl")
            or endpoint_details.get("url")
            or self.DEFAULT_INFERENCE_URL
        )

        inference_key = endpoint_details.get("inferenceApiKey") or {}
        inference_headers: dict[str, str] = {"Content-Type": "application/json"}
        if isinstance(inference_key, dict) and inference_key.get("name") and inference_key.get("value"):
            inference_headers[str(inference_key["name"])] = str(inference_key["value"])
        elif isinstance(inference_key, str) and inference_key:
            inference_headers["Authorization"] = inference_key
        else:
            # Some account/pipeline responses use an Authorization field directly.
            auth_value = endpoint_details.get("authorization") or endpoint_details.get("Authorization")
            if auth_value:
                inference_headers["Authorization"] = str(auth_value)
        return service_id, inference_headers, str(callback_url)

    def _compute(
        self,
        task_type: str,
        language: dict[str, str],
        task_config: dict[str, Any],
        input_data: dict[str, Any],
    ) -> dict[str, Any]:
        service_id, headers, callback_url = self._pipeline_details(task_type, language)
        config = {"language": language, "serviceId": service_id, **task_config}
        payload = {
            "pipelineTasks": [{"taskType": task_type, "config": config}],
            "inputData": input_data,
        }
        return self._request_json(callback_url, headers=headers, payload=payload)

    @staticmethod
    def _first_output(response: dict[str, Any]) -> dict[str, Any]:
        tasks = response.get("pipelineResponse") or []
        if not tasks:
            raise BhashiniError(f"BHASHINI response did not contain pipelineResponse: {response}")
        outputs = tasks[0].get("output") or []
        if not outputs:
            raise BhashiniError(f"BHASHINI response did not contain text output: {response}")
        return outputs[0]

    def transcribe(
        self,
        audio_bytes: bytes,
        source_language: str,
        audio_format: str = "wav",
        sampling_rate: int = 16000,
    ) -> str:
        if not audio_bytes:
            raise BhashiniError("The recorded audio is empty. Please record again.")
        encoded = base64.b64encode(audio_bytes).decode("ascii")
        response = self._compute(
            "asr",
            {"sourceLanguage": source_language},
            {"audioFormat": audio_format, "samplingRate": sampling_rate},
            {"audio": [{"audioContent": encoded}]},
        )
        output = self._first_output(response)
        text = output.get("source") or output.get("target") or output.get("text")
        if not text:
            raise BhashiniError("Speech recognition returned no text. Try speaking more clearly or selecting the correct language.")
        return str(text)

    def translate(self, text: str, source_language: str, target_language: str) -> str:
        clean_text = text.strip()
        if not clean_text:
            raise BhashiniError("Enter or record some text before translating.")
        if source_language == target_language:
            return clean_text
        language = {"sourceLanguage": source_language, "targetLanguage": target_language}
        response = self._compute(
            "translation",
            language,
            {},
            {"input": [{"source": clean_text}]},
        )
        output = self._first_output(response)
        translated = output.get("target") or output.get("source") or output.get("text")
        if not translated:
            raise BhashiniError("Translation returned no text. Check that this language pair is enabled for your account.")
        return str(translated)

    def synthesize(self, text: str, language_code: str) -> bytes:
        clean_text = text.strip()
        if not clean_text:
            raise BhashiniError("There is no text to speak.")
        response = self._compute(
            "tts",
            {"sourceLanguage": language_code},
            {"audioFormat": "wav", "encoding": "base64", "samplingRate": 22050, "gender": "female"},
            {"input": [{"source": clean_text}]},
        )
        tasks = response.get("pipelineResponse") or []
        audio_items = tasks[0].get("audio") or [] if tasks else []
        if not audio_items or not audio_items[0].get("audioContent"):
            raise BhashiniError("Text-to-speech did not return audio. Try a shorter sentence or a supported language.")
        try:
            return base64.b64decode(audio_items[0]["audioContent"])
        except (ValueError, TypeError) as exc:
            raise BhashiniError("BHASHINI returned audio that could not be decoded.") from exc
