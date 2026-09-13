"""Stable, non-sensitive errors exposed by the broker."""

from dataclasses import dataclass


@dataclass
class BrokerError(Exception):
    """An actionable error safe to return to an MCP client."""

    code: str
    message: str
    status: int | None = None

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


def map_http_error(status: int) -> BrokerError:
    """Map provider HTTP statuses without including response secrets."""
    if status in (401, 403):
        return BrokerError("authentication_error", "Provider authentication or permission was rejected", status)
    if status == 429:
        return BrokerError("rate_limited", "Provider rate limit exceeded", status)
    if 400 <= status < 500:
        return BrokerError("provider_error", "Provider rejected the request", status)
    return BrokerError("network_error", "Provider service failed", status)
