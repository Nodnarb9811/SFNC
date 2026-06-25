"""Configuration loading for the TryBooking daily report.

All settings come from environment variables (optionally loaded from a local
``.env`` file). Nothing secret is hard-coded so credentials never end up in
version control.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

try:  # python-dotenv is optional but convenient
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv is a soft dependency
    pass


class ConfigError(RuntimeError):
    """Raised when required configuration is missing."""


def _require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ConfigError(
            f"Missing required environment variable: {name}. "
            f"Copy .env.example to .env and fill it in."
        )
    return value


@dataclass
class ApiConfig:
    api_key: str
    secret: str
    base_url: str


@dataclass
class EmailConfig:
    to_addr: str
    from_addr: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    security: str  # "tls" | "ssl" | "none"


def load_api_config() -> ApiConfig:
    return ApiConfig(
        api_key=_require("TRYBOOKING_API_KEY"),
        secret=_require("TRYBOOKING_SECRET"),
        base_url=os.environ.get("TRYBOOKING_API_BASE", "https://api.trybooking.com").rstrip("/"),
    )


def load_email_config() -> EmailConfig:
    return EmailConfig(
        to_addr=os.environ.get("REPORT_TO", "shop@ssfnc.com.au"),
        from_addr=os.environ.get("REPORT_FROM", "reports@ssfnc.com.au"),
        smtp_host=_require("SMTP_HOST"),
        smtp_port=int(os.environ.get("SMTP_PORT", "587")),
        smtp_user=_require("SMTP_USER"),
        smtp_password=_require("SMTP_PASSWORD"),
        security=os.environ.get("SMTP_SECURITY", "tls").lower(),
    )
