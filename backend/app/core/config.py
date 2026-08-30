"""Application configuration, read from environment variables (see .env.example)."""

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> backend/. Resolved absolutely rather than
# relying on the process's current working directory: uvicorn/pytest/a
# preview-harness launcher can each start this process from a different
# cwd, and a bare relative "env_file=.env" (or a relative
# firebase_service_account_path in .env) would then silently fail to load
# — no error, just every setting falling back to its default. That exact
# failure mode was hit in practice (Phase "registration" work): CORRECT
# emulator/service-account .env values existed but were never read, so the
# Firebase Admin SDK fell through to ApplicationDefault() and crashed with
# a "Your default credentials were not found" error that had nothing to do
# with the actual misconfiguration.
_BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_BACKEND_ROOT / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    # API
    api_host: str = "0.0.0.0"  # noqa: S104 -- intentional dev/container bind-all default
    api_port: int = 8000
    api_cors_origins: str = "http://localhost:5173"
    log_level: str = "INFO"

    # Firebase
    firebase_project_id: str = "timeforge-dev"
    firebase_service_account_path: str | None = None
    firestore_emulator_host: str | None = None
    firebase_auth_emulator_host: str | None = None

    @field_validator("firebase_service_account_path")
    @classmethod
    def _resolve_service_account_path(cls, value: str | None) -> str | None:
        """A relative path in .env (e.g. `./secrets/foo.json`) is meant
        relative to backend/, not whatever the process's cwd happens to
        be — same reasoning as `_BACKEND_ROOT` above."""
        if not value:
            return value
        path = Path(value)
        return str(path) if path.is_absolute() else str(_BACKEND_ROOT / path)

    # Scheduling engine defaults
    scheduling_timeout_seconds: float = 60.0
    scheduling_random_seed: int = 42

    # Registration: email verification (SMTP). Blank username/password
    # means "no real provider configured" — the email sender falls back to
    # logging the code instead of sending it, which is what local dev and
    # tests run against (see app/infrastructure/email/sender.py).
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_from_name: str = "TimeForge"

    # Registration: verification-code lifecycle.
    verification_code_ttl_minutes: int = 10
    verification_code_max_attempts: int = 5

    # Registration: rate limits (per caller, in-process — see
    # app/core/rate_limit.py for the single-node scope note).
    register_rate_limit_per_hour: int = 5
    resend_code_rate_limit_per_15min: int = 3

    # Registration: password policy.
    password_require_symbol: bool = True
    # Checked against the HaveIBeenPwned Pwned Passwords API (k-anonymity —
    # only a SHA-1 prefix ever leaves this process, never the password
    # itself). Best-effort: a network failure logs a warning and allows
    # registration rather than making account creation depend on a third
    # party's uptime (see app/core/security.py).
    password_check_breached: bool = True

    # Registration: reCAPTCHA v2 (checkbox). Blank secret key means "no real
    # provider configured" — verification is skipped (logged), same
    # dev-fallback shape as the SMTP settings above. Get a site/secret key
    # pair at https://www.google.com/recaptcha/admin.
    recaptcha_secret_key: str | None = None

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
