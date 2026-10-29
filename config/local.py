"""Robot Framework variables sourced from environment variables."""

from __future__ import annotations

import os


def _read_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    raise ValueError(f"{name} must be true or false.")


PORTAL_URL = os.environ.get("PORTAL_URL", "").strip().rstrip("/")
BROWSER = os.environ.get("BROWSER", "chrome").strip().lower()
HEADLESS = _read_bool("HEADLESS", True)
CI = _read_bool("CI", False)
WINDOW_SIZE = os.environ.get("WINDOW_SIZE", "1440x1000").strip()
TIMEOUT = int(os.environ.get("TIMEOUT", "10"))
if PORTAL_URL:
    PORTAL_USERNAME = os.environ.get("PORTAL_USERNAME", "")
    PORTAL_PASSWORD = os.environ.get("PORTAL_PASSWORD", "")
else:
    PORTAL_USERNAME = os.environ.get("PORTAL_USERNAME", "member@example.test")
    PORTAL_PASSWORD = os.environ.get("PORTAL_PASSWORD", "MockBenefits!2026")
INVALID_EMAIL = "locked-member@example.test"
INVALID_PASSWORD = "DisabledMember!2026"
