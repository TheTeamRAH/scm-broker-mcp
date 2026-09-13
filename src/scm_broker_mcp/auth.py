"""Environment-only credential loading for supported SCM providers.

Examples:
    Input: ``provider="github"`` with a runtime-injected token.
    Output: A redacted :class:`Credentials` object.
"""

import os
from dataclasses import dataclass

from .errors import BrokerError


@dataclass(frozen=True, repr=False)
class Credentials:
    """Credentials loaded for one provider without exposing secret values.

    Args:
        token: Provider API token. It must come from secret injection.
        email: Bitbucket account email, or ``None`` for GitHub.

    Returns:
        A value object whose representation is always redacted.

    Examples:
        Input: ``Credentials(token="runtime-secret")``.
        Output: ``repr(credentials) == "Credentials(<redacted>)"``.
    """

    token: str
    email: str | None = None

    def __repr__(self) -> str:
        """Return a representation that excludes token and email values.

        Returns:
            The constant string ``"Credentials(<redacted>)"``.

        Examples:
            Input: credentials containing any token or email.
            Output: ``"Credentials(<redacted>)"``.
        """
        return "Credentials(<redacted>)"


def load_credentials(provider: str) -> Credentials:
    """Load environment credentials for GitHub or Bitbucket Cloud.

    Args:
        provider: Provider key, either ``"github"`` or ``"bitbucket"``.

    Returns:
        A :class:`Credentials` object populated from environment variables.

    Raises:
        BrokerError: If the provider is unsupported or required variables are
            absent. Error messages never contain credential values.

    Examples:
        Input: ``provider="github"`` with ``GITHUB_TOKEN`` injected.
        Output: ``Credentials(token="...", email=None)`` (redacted in repr).
    """
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
