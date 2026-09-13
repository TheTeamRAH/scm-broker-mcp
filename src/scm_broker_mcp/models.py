"""Provider-neutral result models and normalization helpers.

Examples:
    Input: ``{"number": 7, "state": "OPEN"}``.
    Output: ``{"id": "7", "state": "open", ...}``.
"""

from typing import Any


def _url(raw: dict[str, Any]) -> str | None:
    """Extract a provider-independent HTML URL from a payload.

    Args:
        raw: Provider response mapping with GitHub or Bitbucket link fields.

    Returns:
        The HTML URL when present, otherwise ``None``.

    Examples:
        Input: ``{"links": {"html": {"href": "https://scm/pr/1"}}}``.
        Output: ``"https://scm/pr/1"``.
    """
    return raw.get("html_url") or raw.get("links", {}).get("html", {}).get("href")


def normalize_item(raw: dict[str, Any], *, include_raw: bool = False) -> dict[str, Any]:
    """Normalize a repository, comment, commit, reviewer, or review item.

    Args:
        raw: Provider item mapping.
        include_raw: Preserve the provider mapping under ``raw`` when true.

    Returns:
        Mapping with ``id``, ``title``, lowercase ``state``, ``url``, and
        optional ``raw`` fields.

    Examples:
        Input: ``{"number": 7, "title": "Fix", "state": "OPEN"}``.
        Output: ``{"id": "7", "title": "Fix", "state": "open", "url": None, "raw": None}``.
    """
    ident = raw.get("number", raw.get("id", raw.get("hash", "")))
    return {"id": str(ident), "title": raw.get("title", ""), "state": str(raw.get("state", "")).lower(), "url": _url(raw), "raw": raw if include_raw else None}


def normalize_pull_request(raw: dict[str, Any], provider: str = "", include_raw: bool = False) -> dict[str, Any]:
    """Normalize a pull-request payload into stable provider-neutral fields.

    Args:
        raw: GitHub or Bitbucket pull-request response mapping.
        provider: Provider name retained for API compatibility.
        include_raw: Preserve the original payload under ``raw`` when true.

    Returns:
        A normalized pull-request mapping with string ``id`` and lowercase
        ``state``.

    Examples:
        Input: ``{"number": 7, "title": "Fix", "state": "OPEN"}``.
        Output: ``{"id": "7", "title": "Fix", "state": "open", "url": None, "raw": None}``.
    """
    result = normalize_item(raw, include_raw=include_raw)
    result["state"] = result["state"].lower()
    return result


def normalize_write(raw: dict[str, Any], provider: str = "", include_raw: bool = False) -> dict[str, Any]:
    """Normalize a state-changing provider response.

    Args:
        raw: Provider response mapping.
        provider: Provider name retained for API compatibility.
        include_raw: Preserve the original payload under ``raw`` when true.

    Returns:
        A normalized result mapping containing stable fields and optional raw data.

    Examples:
        Input: ``{"id": 9, "state": "MERGED"}``.
        Output: ``{"id": "9", "title": "", "state": "merged", "url": None, "raw": None}``.
    """
    return normalize_item(raw, include_raw=include_raw)


def normalize_page(payload: Any, *, page: int, page_size: int, include_raw: bool = False) -> dict[str, Any]:
    """Normalize GitHub arrays and Bitbucket ``values`` pages.

    Args:
        payload: A provider list, either a list or a mapping with ``values``.
        page: Provider-neutral one-based page number.
        page_size: Requested number of items per page.
        include_raw: Preserve each provider item when true.

    Returns:
        Mapping with normalized ``items``, ``page``, ``page_size``, and boolean
        ``has_more`` fields.

    Examples:
        Input: ``payload=[{"id": 1}], page=1, page_size=30``.
        Output: ``{"items": [{"id": "1", ...}], "page": 1, "page_size": 30, "has_more": False}``.
    """
    values = payload.get("values", []) if isinstance(payload, dict) else payload if isinstance(payload, list) else []
    return {"items": [normalize_item(item, include_raw=include_raw) for item in values], "page": page, "page_size": page_size, "has_more": bool(payload.get("next")) if isinstance(payload, dict) else False}
