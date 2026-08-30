"""Password-strength policy, verification-code helpers, breach-checking,
and reCAPTCHA verification for self-service registration. Kept
dependency-free (stdlib `hashlib`/`secrets`/`urllib` only) rather than
pulling in `passlib`/`httpx` for a handful of small, occasional HTTP calls.
"""

import hashlib
import json
import logging
import re
import secrets
import urllib.error
import urllib.parse
import urllib.request

from app.core.errors import ValidationError

logger = logging.getLogger(__name__)

_MIN_LENGTH = 8
_REQUEST_TIMEOUT_SECONDS = 5
_PWNED_PASSWORDS_RANGE_URL = "https://api.pwnedpasswords.com/range/"
_RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"


def validate_password_strength(password: str, *, require_symbol: bool = True) -> None:
    """Raises ValidationError listing every unmet rule at once (so the UI
    can show them all together instead of one round-trip per rule)."""
    problems: list[str] = []
    if len(password) < _MIN_LENGTH:
        problems.append(f"at least {_MIN_LENGTH} characters")
    if not re.search(r"[a-z]", password):
        problems.append("a lowercase letter")
    if not re.search(r"[A-Z]", password):
        problems.append("an uppercase letter")
    if not re.search(r"\d", password):
        problems.append("a digit")
    if require_symbol and not re.search(r"[^A-Za-z0-9]", password):
        problems.append("a symbol (e.g. !@#$%)")
    if problems:
        raise ValidationError(
            "Password does not meet the minimum strength requirements",
            details={"requirements": problems},
        )


def check_password_not_breached(password: str) -> None:
    """Checks the password against the HaveIBeenPwned Pwned Passwords API
    using k-anonymity: only the first 5 hex characters of the password's
    SHA-1 hash are ever sent, never the password or its full hash — HIBP
    returns every suffix sharing that prefix, and the match happens
    locally. A network failure or non-200 response is logged and treated
    as "couldn't check" rather than blocking registration; account
    creation shouldn't depend on a third party's uptime."""
    sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()  # noqa: S324 -- HIBP's own protocol, not used for secrecy
    prefix, suffix = sha1[:5], sha1[5:]

    try:
        request = urllib.request.Request(  # noqa: S310 -- fixed https:// constant, not user input
            _PWNED_PASSWORDS_RANGE_URL + prefix, headers={"Add-Padding": "true"}
        )
        with urllib.request.urlopen(request, timeout=_REQUEST_TIMEOUT_SECONDS) as response:  # noqa: S310
            body = response.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError) as exc:
        logger.warning("Pwned Passwords check unavailable, allowing registration: %s", exc)
        return

    for line in body.splitlines():
        line_suffix, _, count = line.partition(":")
        if line_suffix == suffix and count.strip() not in ("", "0"):
            raise ValidationError(
                "This password has appeared in a known data breach — please choose a different one",
            )


def verify_recaptcha(token: str, *, secret_key: str | None) -> None:
    """Verifies a reCAPTCHA v2 response token against Google's siteverify
    endpoint. A blank secret_key means no real provider is configured
    (local dev/tests) — verification is skipped and logged, the same
    dev-fallback shape as the SMTP sender."""
    if not secret_key:
        logger.warning("reCAPTCHA not configured — skipping verification (dev mode).")
        return

    data = urllib.parse.urlencode({"secret": secret_key, "response": token}).encode("ascii")
    try:
        with urllib.request.urlopen(  # noqa: S310 -- fixed https:// constant, not user input
            _RECAPTCHA_VERIFY_URL, data=data, timeout=_REQUEST_TIMEOUT_SECONDS
        ) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ValidationError("Could not verify reCAPTCHA — please try again") from exc

    if not result.get("success"):
        raise ValidationError("reCAPTCHA verification failed — please try again")


def generate_numeric_code(length: int = 6) -> str:
    return "".join(str(secrets.randbelow(10)) for _ in range(length))


def hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()
