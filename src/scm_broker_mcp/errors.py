"""Stable, non-sensitive errors exposed by the broker.

Examples:
    Input: HTTP status ``429``.
    Output: A ``rate_limited`` :class:`BrokerError`.
"""

from dataclasses import dataclass


@dataclass
class BrokerError(Exception):
    """An actionable error safe to return to an MCP client.

    Args:
        code: Stable machine-readable error category.
        message: Safe human-readable explanation.
        status: Optional provider HTTP status.

    Returns:
        An exception whose string form contains only the supplied safe fields.

    Examples:
        Input: ``BrokerError("rate_limited", "Try again later", 429)``.
        Output: ``str(error) == "rate_limited: Try again later"``.
    """

    code: str
    message: str
    status: int | None = None

    def __str__(self) -> str:
        """Format the stable code and message for logs or clients.

        Returns:
            A ``"<code>: <message>"`` string without response payloads.

        Examples:
            Input: ``BrokerError("provider_error", "Rejected")``.
            Output: ``"provider_error: Rejected"``.
        """
        return f"{self.code}: {self.message}"


def map_http_error(status: int) -> BrokerError:
    """Map provider HTTP statuses without including response secrets.

    Args:
        status: HTTP status returned by a provider.

    Returns:
        A stable :class:`BrokerError` with a non-sensitive message.

    Examples:
        Input: ``status=429``.
        Output: ``BrokerError(code="rate_limited", status=429)``.
    """
    if status in (401, 403):
        return BrokerError("authentication_error", "Provider authentication or permission was rejected", status)
    if status == 429:
        return BrokerError("rate_limited", "Provider rate limit exceeded", status)
    if 400 <= status < 500:
        return BrokerError("provider_error", "Provider rejected the request", status)
    return BrokerError("network_error", "Provider service failed", status)
