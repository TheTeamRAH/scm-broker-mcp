"""Environment-only credential loading."""

import os
from dataclasses import dataclass

from .errors import BrokerError


@dataclass(frozen=True, repr=False)
class Credentials:
    """Provider credential, deliberately omitted from repr."""

    token: str
    email: str | None = None

    def __repr__(self) -> str:
        return "Credentials(<redacted>)"


def load_credentials(provider: str) -> Credentials:
    """Load credentials from the process environment."""
    if provider == "github":
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise BrokerError("missing_credentials", "GITHUB_TOKEN is required")
        return Credentials(token=token)
    if provider == "bitbucket":
        email, token = os.getenv("BITBUCKET_EMAIL"), os.getenv("BITBUCKET_API_TOKEN")
        if not email or not token:
            raise BrokerError("missing_credentials", "BITBUCKET_EMAIL and BITBUCKET_API_TOKEN are required")
        return Credentials(token=token, email=email)
    raise BrokerError("invalid_provider", "provider must be 'github' or 'bitbucket'")
