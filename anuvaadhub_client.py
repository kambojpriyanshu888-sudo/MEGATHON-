import requests


class AnuvaadHubError(RuntimeError):
    pass


class AnuvaadHubASRClient:
    def __init__(self, endpoint: str, access_token: str = ""):
        self.endpoint = endpoint.strip()
        self.access_token = access_token.strip()

    def transcribe(self, audio_bytes: bytes) -> str:
        if not self.endpoint:
            raise AnuvaadHubError(
                "Missing ANUVAADHUB_ASR_URL in your .env file."
            )

        if not audio_bytes:
            raise AnuvaadHubError("The audio recording is empty.")

        headers = {"Accept": "application/json"}

        if self.access_token:
            headers["access-token"] = self.access_token

        files = {
            "audio_file": (
                "recording.wav",
                audio_bytes,
                "audio/wav",
            )
        }

        try:
            response = requests.post(
                self.endpoint,
                headers=headers,
                files=files,
                timeout=60,
            )
        except requests.RequestException as exc:
            raise AnuvaadHubError(
                f"Could not connect to AnuvaadHub: {type(exc).__name__}"
            ) from exc

        if not response.ok:
            details = response.text[:1000]
            if self.access_token:
                details = details.replace(
                    self.access_token, "[REDACTED]"
                )
            raise AnuvaadHubError(
                f"AnuvaadHub HTTP {response.status_code}: {details}"
            )

        try:
            result = response.json()
        except ValueError:
            result = response.text.strip()
            if result:
                return result
            raise AnuvaadHubError(
                "AnuvaadHub returned an empty response."
            )

        transcript = self._find_text(result)

        if transcript:
            return transcript

        raise AnuvaadHubError(
            "The request succeeded, but the transcript field "
            "was not recognized. Check the model response format."
        )

    @classmethod
    def _find_text(cls, value):
        if isinstance(value, str):
            return value.strip()

        if isinstance(value, list):
            for item in value:
                found = cls._find_text(item)
                if found:
                    return found
            return ""

        if isinstance(value, dict):
            preferred_keys = (
                "text",
                "transcript",
                "transcription",
                "output_text",
                "recognized_text",
                "result",
                "data",
                "output",
                "results",
                "pipelineResponse",
            )

            for key in preferred_keys:
                if key in value:
                    found = cls._find_text(value[key])
                    if found:
                        return found

        return ""
