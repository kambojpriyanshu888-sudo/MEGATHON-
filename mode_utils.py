"""Language-independent helper logic for the accessible mode chooser."""


def detect_mode(text: str) -> str | None:
    """Best-effort phrase matching for choosing an accessibility mode by voice."""
    value = text.casefold()
    blind_words = [
        "blind", "visually impaired", "low vision", "दृष्टिहीन", "अंधा", "अंधी",
        "कम दिखाई", "नेत्रहीन", "नज़र की समस्या", "ਅੰਨ੍ਹਾ", "ਅੰਨ੍ਹੀ", "ਨਜ਼ਰ ਦੀ ਸਮੱਸਿਆ",
    ]
    deaf_words = [
        "deaf", "hard of hearing", "cannot hear", "can't hear", "बहरा", "बहरी",
        "सुन नहीं", "सुनने में कठिनाई", "ਬਹਿਰਾ", "ਸੁਣ ਨਹੀਂ", "ਸੁਣਨ ਵਿੱਚ ਮੁਸ਼ਕਲ",
    ]
    speech_words = [
        "non-speaking", "cannot speak", "can't speak", "speech difficulty", "mute",
        "गूंगा", "गूंगी", "बोल नहीं", "बोलने में कठिनाई", "ਬੋਲ ਨਹੀਂ",
        "ਬੋਲਣ ਵਿੱਚ ਮੁਸ਼ਕਲ", "ਗੂੰਗਾ", "ਗੂੰਗੀ",
    ]
    if any(word in value for word in blind_words):
        return "blind"
    if any(word in value for word in deaf_words):
        return "deaf"
    if any(word in value for word in speech_words):
        return "speech"
    return None
