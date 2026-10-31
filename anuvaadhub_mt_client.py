import os
import requests


class AnuvaadHubMTError(RuntimeError):
    pass


class AnuvaadHubMTClient:
    DIRECTIONS = {
        ("en", "hi"): "EN_HI",
        ("hi", "en"): "HI_EN",
        ("en", "pa"): "EN_PA",
        ("pa", "en"): "PA_EN",
        ("hi", "pa"): "HI_PA",
        ("pa", "hi"): "PA_HI",
    }

    def translate(self, text, source_code, target_code):
        text = text.strip()
        source = source_code.lower().split("-")[0]
        target = target_code.lower().split("-")[0]

        if not text:
            raise AnuvaadHubMTError("There is no text to translate.")

        if source == target:
            return text

        direction = self.DIRECTIONS.get((source, target))
        if not direction:
            raise AnuvaadHubMTError(
                f"Unsupported translation: {source} to {target}."
            )

        prefix = f"ANUVAADHUB_MT_{direction}"
        endpoint = os.getenv(f"{prefix}_URL", "").strip()
        token = os.getenv(f"{prefix}_TOKEN", "").strip()

        if not endpoint:
            raise AnuvaadHubMTError(
                f"Missing {prefix}_URL in your .env file."
            )

        headers = {"Accept": "application/json"}
        if token:
            headers["access-token"] = token

        try:
            response = requests.post(
                endpoint,
                headers=headers,
                json={"input_text": text},
                timeout=60,
            )
        except requests.RequestException as exc:
            raise AnuvaadHubMTError(
                f"Could not connect to AnuvaadHub: {type(exc).__name__}."
            ) from exc

        if not response.ok:
            details = response.text[:1000]
            if token:
                details = details.replace(token, "[REDACTED]")
            raise AnuvaadHubMTError(
                f"Translation API returned HTTP {response.status_code}: "
                f"{details}"
            )

        try:
            result = response.json()
        except ValueError:
            result = response.text.strip()
            if result:
                return result
            raise AnuvaadHubMTError("The translation response was empty.")

        if isinstance(result, dict) and (
            str(result.get("status", "")).lower() == "error"
            or result.get("error")
        ):
            detail = result.get("message") or result.get("error")
            if detail:
                raise AnuvaadHubMTError(f"Translation API error: {detail}")

        translated = self._extract_text(result)
        if translated:
            return translated

        if isinstance(result, dict):
            keys = ", ".join(result.keys())
            raise AnuvaadHubMTError(
                "The API responded, but its translation field was not "
                f"recognized. Response keys: {keys}"
            )

        raise AnuvaadHubMTError(
            "The API responded, but no translation text was found."
        )

    @classmethod
    def _extract_text(cls, value):
        if isinstance(value, str):
            return value.strip()

        if isinstance(value, list):
            for item in value:
                found = cls._extract_text(item)
                if found:
                    return found
            return ""

        if isinstance(value, dict):
            preferred_keys = (
                "translated_text",
                "translation_text",
                "translation",
                "output_text",
                "generated_text",
                "prediction",
                "text",
                "output",
                "result",
                "results",
                "data",
            )

            for key in preferred_keys:
                if key in value:
                    found = cls._extract_text(value[key])
                    if found:
                        return found

        return ""
