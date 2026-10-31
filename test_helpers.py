"""Offline tests for the mode selector's phrase matching."""
from mode_utils import detect_mode


def test_mode_detection():
    assert detect_mode("I am blind") == "blind"
    assert detect_mode("मैं सुन नहीं सकता") == "deaf"
    assert detect_mode("I cannot speak") == "speech"
    assert detect_mode("I need help with a menu") is None
