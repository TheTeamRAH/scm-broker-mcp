"""Provider-neutral result models and normalization helpers."""

from typing import Any


def _url(raw: dict[str, Any]) -> str | None:
    """Extract a provider-independent HTML URL."""
    return raw.get("html_url") or raw.get("links", {}).get("html", {}).get("href")


def normalize_item(raw: dict[str, Any], *, include_raw: bool = False) -> dict[str, Any]:
    """Normalize a repository, comment, commit, reviewer, or review item."""
    ident = raw.get("number", raw.get("id", raw.get("hash", "")))
    return {"id": str(ident), "title": raw.get("title", ""), "state": str(raw.get("state", "")).lower(), "url": _url(raw), "raw": raw if include_raw else None}


def normalize_pull_request(raw: dict[str, Any], provider: str = "", include_raw: bool = False) -> dict[str, Any]:
    """Normalize a pull-request payload into stable fields."""
    result = normalize_item(raw, include_raw=include_raw)
    result["state"] = result["state"].lower()
    return result


def normalize_write(raw: dict[str, Any], provider: str = "", include_raw: bool = False) -> dict[str, Any]:
    """Normalize a state-changing provider response."""
    return normalize_item(raw, include_raw=include_raw)


def normalize_page(payload: Any, *, page: int, page_size: int, include_raw: bool = False) -> dict[str, Any]:
    """Normalize GitHub arrays and Bitbucket ``values`` pages."""
    values = payload.get("values", []) if isinstance(payload, dict) else payload if isinstance(payload, list) else []
    return {"items": [normalize_item(item, include_raw=include_raw) for item in values], "page": page, "page_size": page_size, "has_more": bool(payload.get("next")) if isinstance(payload, dict) else False}
