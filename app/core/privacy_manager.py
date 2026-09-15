"""
PrivacyManager doesn't "do" much computationally -- its purpose is to be the
single source of truth for BlinkGuard's privacy commitments, surfaced in the
Privacy page, so the guarantees are documented in one place rather than
scattered as comments.
"""

PRIVACY_STATEMENT = (
    "BlinkGuard processes your camera feed entirely on your own computer.\n\n"
    "What happens to each camera frame:\n"
    "  1. A frame is captured from your webcam.\n"
    "  2. It is analyzed locally to find your eyes and estimate blinking.\n"
    "  3. Only numeric results (blink yes/no, eye-openness value) are kept.\n"
    "  4. The frame itself is immediately discarded.\n\n"
    "What BlinkGuard never does:\n"
    "  - Never saves photos, video, or camera recordings.\n"
    "  - Never uploads camera data anywhere.\n"
    "  - Never sends anything to an external server or third-party API for "
    "blink detection.\n\n"
    "What is stored locally (in a SQLite database on your machine):\n"
    "  - Session start/end times\n"
    "  - Screen time, active time, and break time (in seconds)\n"
    "  - Blink counts and blink-rate aggregates\n"
    "  - Longest no-blink duration and low-blink-period counts\n\n"
    "None of this data leaves your computer unless you explicitly export or "
    "back it up yourself."
)

MEDICAL_DISCLAIMER = (
    "BlinkGuard is designed to encourage healthy screen habits and regular "
    "blinking. It is not a medical device. It does not diagnose, treat, or "
    "guarantee protection from any eye condition or disease. If you "
    "experience eye pain, vision changes, or persistent discomfort, please "
    "consult an eye care professional."
)


class PrivacyManager:
    @staticmethod
    def get_privacy_statement() -> str:
        return PRIVACY_STATEMENT

    @staticmethod
    def get_medical_disclaimer() -> str:
        return MEDICAL_DISCLAIMER
