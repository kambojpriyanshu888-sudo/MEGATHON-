import requests


class AnuvaadHubTTSError(RuntimeError):
    pass


class AnuvaadHubTTSClient:
    def __init__(
        self,
        endpoint: str,
        access_token: str = "",
        settings_prefix: str = "ANUVAADHUB_TTS_EN",
    ):
        self.endpoint = endpoint.strip()
        self.access_token = access_token.strip()
        self.settings_prefix = settings_prefix

    @property
    def is_configured(self) -> bool:
        return bool(self.endpoint and self.access_token)

    def synthesize(self, text: str, gender: str = "female") -> bytes:
        text = text.strip()
        gender = gender.strip().lower()

        if not text:
            raise AnuvaadHubTTSError("There is no text to speak.")
        if gender not in {"male", "female"}:
            raise AnuvaadHubTTSError("Choose either a male or female voice.")
        if not self.endpoint:
            raise AnuvaadHubTTSError(
                f"Missing {self.settings_prefix}_URL in your .env file."
            )
        if not self.access_token:
            raise AnuvaadHubTTSError(
                f"Missing {self.settings_prefix}_TOKEN in your .env file."
            )

        try:
            response = requests.post(
                self.endpoint,
                headers={"Accept": "application/json", "access-token": self.access_token},
                json={"text": text, "gender": gender},
                timeout=60,
            )
        except requests.RequestException as exc:
            raise AnuvaadHubTTSError(
                f"Could not connect to AnuvaadHub TTS: {type(exc).__name__}."
            ) from exc

        if not response.ok:
            details = response.text[:1000]
            details = details.replace(self.access_token, "[REDACTED]")
            raise AnuvaadHubTTSError(
                f"TTS API returned HTTP {response.status_code}: {details}"
            )

        try:
            result = response.json()
        except ValueError as exc:
            raise AnuvaadHubTTSError("TTS API returned an invalid JSON response.") from exc

        if not isinstance(result, dict):
            raise AnuvaadHubTTSError("TTS API returned an unexpected response.")

        if str(result.get("status", "")).lower() != "success" or result.get("error"):
            message = result.get("message") or result.get("error") or "Unknown TTS error."
            raise AnuvaadHubTTSError(f"TTS API error: {message}")

        data = result.get("data")
        audio_url = data.get("s3_url") if isinstance(data, dict) else None
        if not audio_url:
            raise AnuvaadHubTTSError("TTS API succeeded but did not return data.s3_url.")
        if not str(audio_url).lower().startswith("https://"):
            raise AnuvaadHubTTSError("TTS API returned an invalid audio URL.")

        try:
            audio_response = requests.get(audio_url, timeout=60)
        except requests.RequestException as exc:
            raise AnuvaadHubTTSError(
                f"Could not download generated speech: {type(exc).__name__}."
            ) from exc

        if not audio_response.ok:
            raise AnuvaadHubTTSError(
                f"Could not download generated speech (HTTP {audio_response.status_code})."
            )
        if not audio_response.content:
            raise AnuvaadHubTTSError("The generated audio file was empty.")

        return audio_response.content
