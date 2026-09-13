"""FastMCP transports and operation-specific tool definitions.

Examples:
    Input: ``{"provider": "github", "repo": "o/r"}`` for a registered tool.
    Output: a provider-neutral result mapping.
"""

import logging
import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from .errors import BrokerError
from .service import BrokerService


class RedactFilter(logging.Filter):
    """Prevent common credential material from entering logs.

    Examples:
        Input: a log record containing an injected token.
        Output: the same record with matching credential values replaced by
        ``"[REDACTED]"``.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact configured credential values in a log record.

        Args:
            record: Mutable logging record to sanitize.

        Returns:
            ``True`` so normal logging continues after sanitization.

        Examples:
            Input: ``LogRecord(msg="token-value", args=())``.
            Output: ``record.msg == "[REDACTED]"`` when the token is configured.
        """
        message = str(record.msg)
        for secret_name in ("GITHUB_TOKEN", "BITBUCKET_API_TOKEN", "BITBUCKET_EMAIL"):
            secret = os.getenv(secret_name)
            if secret:
                message = message.replace(secret, "[REDACTED]")
        record.msg, record.args = message, ()
        return True


mcp = FastMCP("scm-broker-mcp", host=os.getenv("SCM_HOST", "127.0.0.1"), port=int(os.getenv("SCM_PORT", "8000")))
service = BrokerService()


async def _run(operation: str, provider: str, repo: str | None = None, pull_request_id: str | None = None, raw: bool = False, **kwargs: Any) -> dict[str, Any]:
    """Execute a tool and convert expected errors to structured results.

    Args:
        operation: Service operation name.
        provider: Provider key.
        repo: Optional repository identity.
        pull_request_id: Optional pull-request identifier.
        raw: Whether to retain provider payloads.
        **kwargs: Operation-specific input shape.

    Returns:
        A result mapping or ``{"error": {"type": ..., "message": ..., "status": ...}}``.

    Examples:
        Input: ``operation="list_repositories", provider="github", page=1``.
        Output: ``{"items": [...], "page": 1, "page_size": 30, "has_more": False}``.
    """
    try:
        return await service.execute(operation, provider, repo, pull_request_id, raw, **kwargs)
    except BrokerError as exc:
        return {"error": {"type": exc.code, "message": exc.message, "status": exc.status}}


@mcp.tool()
async def list_repositories(provider: str, workspace: str | None = None, page: int = 1, page_size: int = 30, raw: bool = False) -> dict[str, Any]:
    """List repositories visible to the authenticated provider account.

    Args:
        provider: ``"github"`` or ``"bitbucket"``.
        workspace: Optional Bitbucket workspace or GitHub repository scope.
        page: One-based page number.
        page_size: Number of results, from 1 through 100.
        raw: Include provider payloads.

    Returns:
        Page mapping with ``items``, ``page``, ``page_size``, and ``has_more``.

    Examples:
        Input: ``{"provider": "github", "page": 1, "page_size": 30}``.
        Output: ``{"items": [{"id": "1", ...}], "page": 1, "page_size": 30, "has_more": False}``.
    """
    return await _run("list_repositories", provider, workspace, raw=raw, page=page, page_size=page_size)


@mcp.tool()
async def list_pull_requests(provider: str, repo: str, state: str = "open", page: int = 1, page_size: int = 30, raw: bool = False) -> dict[str, Any]:
    """List pull requests in a repository.

    Args:
        provider: Provider key.
        repo: Repository in ``owner/name`` or ``workspace/slug`` form.
        state: Provider pull-request state filter.
        page: One-based page number.
        page_size: Number of results, from 1 through 100.
        raw: Include provider payloads.

    Returns:
        Page mapping with normalized pull-request items.

    Examples:
        Input: ``{"provider": "github", "repo": "o/r", "state": "open"}``.
        Output: ``{"items": [{"id": "7", "state": "open", ...}], ...}``.
    """
    return await _run("list_pull_requests", provider, repo, raw=raw, state=state, page=page, page_size=page_size)


@mcp.tool()
async def get_pull_request(provider: str, repo: str, pull_request_id: str, raw: bool = False) -> dict[str, Any]:
    """Get one pull request.

    Args:
        provider: Provider key.
        repo: Repository identity.
        pull_request_id: Provider pull-request identifier.
        raw: Include the provider payload.

    Returns:
        Normalized pull-request mapping with ``id``, ``title``, ``state``, and ``url``.

    Examples:
        Input: ``{"provider": "github", "repo": "o/r", "pull_request_id": "7"}``.
        Output: ``{"id": "7", "title": "Fix", "state": "open", ...}``.
    """
    return await _run("get_pull_request", provider, repo, pull_request_id, raw=raw)


@mcp.tool()
async def get_pull_request_diff(provider: str, repo: str, pull_request_id: str) -> dict[str, Any]:
    """Get a pull request unified diff.

    Args:
        provider: Provider key.
        repo: Repository identity.
        pull_request_id: Provider pull-request identifier.

    Returns:
        Mapping shaped as ``{"diff": str, "raw": None}``.

    Examples:
        Input: ``{"provider": "github", "repo": "o/r", "pull_request_id": "7"}``.
        Output: ``{"diff": "diff --git ...", "raw": None}``.
    """
    return await _run("get_pull_request_diff", provider, repo, pull_request_id)


@mcp.tool()
async def list_pull_request_commits(provider: str, repo: str, pull_request_id: str, page: int = 1, page_size: int = 30, raw: bool = False) -> dict[str, Any]:
    """List commits associated with a pull request.

    Args:
        provider: Provider key; ``repo`` and ``pull_request_id`` identify the PR.
        page: One-based page number.
        page_size: Number of results, from 1 through 100.
        raw: Include provider payloads.

    Returns:
        Page mapping containing normalized commit items.

    Examples:
        Input: ``{"provider": "github", "repo": "o/r", "pull_request_id": "7"}``.
        Output: ``{"items": [{"id": "abc", ...}], "page": 1, ...}``.
    """
    return await _run("list_pull_request_commits", provider, repo, pull_request_id, raw, page=page, page_size=page_size)


@mcp.tool()
async def create_pull_request(provider: str, repo: str, title: str, source_branch: str, target_branch: str, description: str = "", raw: bool = False) -> dict[str, Any]:
    """Create a pull request from one branch into another.

    Args:
        provider: Provider key.
        repo: Repository identity.
        title: Pull-request title.
        source_branch: Source branch name.
        target_branch: Destination branch name.
        description: Optional body text.
        raw: Include the provider payload.

    Returns:
        Normalized write-result mapping with identifier, state, and URL fields.

    Examples:
        Input: ``{"repo": "o/r", "title": "Fix", "source_branch": "bug", "target_branch": "main"}``.
        Output: ``{"id": "8", "state": "open", "url": "https://...", ...}``.
    """
    return await _run("create_pull_request", provider, repo, raw=raw, title=title, source_branch=source_branch, target_branch=target_branch, description=description)


@mcp.tool()
async def update_pull_request(provider: str, repo: str, pull_request_id: str, title: str | None = None, description: str | None = None, raw: bool = False) -> dict[str, Any]:
    """Update a pull-request title or description.

    Args:
        provider: Provider key.
        repo: Repository identity.
        pull_request_id: Provider pull-request identifier.
        title: Optional replacement title.
        description: Optional replacement body.
        raw: Include the provider payload.

    Returns:
        Normalized write-result mapping.

    Examples:
        Input: ``{"repo": "o/r", "pull_request_id": "7", "title": "Updated"}``.
        Output: ``{"id": "7", "title": "Updated", "state": "open", ...}``.
    """
    return await _run("update_pull_request", provider, repo, pull_request_id, raw, title=title, description=description)


@mcp.tool()
async def update_pull_request_reviewers(provider: str, repo: str, pull_request_id: str, reviewers: list[str]) -> dict[str, Any]:
    """Request reviewers when supported by the provider.

    Args:
        provider: Provider key.
        repo: Repository identity.
        pull_request_id: Provider pull-request identifier.
        reviewers: Reviewer usernames or account identifiers.

    Returns:
        Normalized provider write-result mapping.

    Examples:
        Input: ``{"repo": "o/r", "pull_request_id": "7", "reviewers": ["alice"]}``.
        Output: ``{"id": "7", "state": "", "raw": None, ...}``.
    """
    return await _run("update_pull_request_reviewers", provider, repo, pull_request_id, reviewers=reviewers)


@mcp.tool()
async def close_pull_request(provider: str, repo: str, pull_request_id: str, raw: bool = False) -> dict[str, Any]:
    """Close or decline a pull request.

    Args:
        provider: Provider key.
        repo: Repository identity.
        pull_request_id: Provider pull-request identifier.
        raw: Include the provider payload.

    Returns:
        Normalized write-result mapping with the resulting state.

    Examples:
        Input: ``{"repo": "o/r", "pull_request_id": "7"}``.
        Output: ``{"id": "7", "state": "closed", ...}``.
    """
    return await _run("close_pull_request", provider, repo, pull_request_id, raw=raw)


@mcp.tool()
async def merge_pull_request(provider: str, repo: str, pull_request_id: str, merge_method: str = "merge", raw: bool = False) -> dict[str, Any]:
    """Merge a pull request using an explicit provider-supported method.

    Args:
        provider: Provider key.
        repo: Repository identity.
        pull_request_id: Provider pull-request identifier.
        merge_method: One of ``merge``, ``squash``, or ``rebase``.
        raw: Include the provider payload.

    Returns:
        Normalized write-result mapping with resulting state and URL.

    Examples:
        Input: ``{"repo": "o/r", "pull_request_id": "7", "merge_method": "squash"}``.
        Output: ``{"id": "7", "state": "merged", ...}``.
    """
    if merge_method not in {"merge", "squash", "rebase"}:
        return {"error": {"type": "invalid_argument", "message": "merge_method must be merge, squash, or rebase", "status": None}}
    return await _run("merge_pull_request", provider, repo, pull_request_id, raw, merge_method=merge_method)


@mcp.tool()
async def add_pull_request_comment(provider: str, repo: str, pull_request_id: str, body: str, raw: bool = False) -> dict[str, Any]:
    """Add a comment to a pull request.

    Args:
        provider: Provider key.
        repo: Repository identity.
        pull_request_id: Provider pull-request identifier.
        body: Comment text.
        raw: Include the provider payload.

    Returns:
        Normalized write-result mapping.

    Examples:
        Input: ``{"repo": "o/r", "pull_request_id": "7", "body": "Looks good"}``.
        Output: ``{"id": "comment-1", "state": "", ...}``.
    """
    return await _run("add_pull_request_comment", provider, repo, pull_request_id, raw, body=body)


@mcp.tool()
async def list_pull_request_comments(provider: str, repo: str, pull_request_id: str, page: int = 1, page_size: int = 30, raw: bool = False) -> dict[str, Any]:
    """List comments attached to a pull request.

    Args:
        provider: Provider key.
        repo: Repository identity.
        pull_request_id: Provider pull-request identifier.
        page: One-based page number.
        page_size: Number of results, from 1 through 100.
        raw: Include provider payloads.

    Returns:
        Page mapping containing normalized comment items.

    Examples:
        Input: ``{"repo": "o/r", "pull_request_id": "7", "page": 1}``.
        Output: ``{"items": [{"id": "comment-1", ...}], ...}``.
    """
    return await _run("list_pull_request_comments", provider, repo, pull_request_id, raw, page=page, page_size=page_size)


@mcp.tool()
async def list_pull_request_reviews(provider: str, repo: str, pull_request_id: str, page: int = 1, page_size: int = 30, raw: bool = False) -> dict[str, Any]:
    """List reviews attached to a pull request.

    Args:
        provider: Provider key.
        repo: Repository identity.
        pull_request_id: Provider pull-request identifier.
        page: One-based page number.
        page_size: Number of results, from 1 through 100.
        raw: Include provider payloads.

    Returns:
        Page mapping containing normalized review items.

    Examples:
        Input: ``{"repo": "o/r", "pull_request_id": "7", "page": 1}``.
        Output: ``{"items": [{"id": "review-1", ...}], ...}``.
    """
    return await _run("list_pull_request_reviews", provider, repo, pull_request_id, raw, page=page, page_size=page_size)


@mcp.tool()
async def submit_pull_request_review(provider: str, repo: str, pull_request_id: str, event: str, body: str = "", raw: bool = False) -> dict[str, Any]:
    """Submit an approve, request-changes, or comment review.

    Args:
        provider: Provider key.
        repo: Repository identity.
        pull_request_id: Provider pull-request identifier.
        event: ``approve``, ``request_changes``, or ``comment``.
        body: Optional review body.
        raw: Include the provider payload.

    Returns:
        Normalized write-result mapping, or a structured error mapping.

    Examples:
        Input: ``{"repo": "o/r", "pull_request_id": "7", "event": "approve"}``.
        Output: ``{"id": "7", "state": "approved", ...}`` or an error shape.
    """
    if event not in {"approve", "request_changes", "comment"}:
        return {"error": {"type": "invalid_argument", "message": "event must be approve, request_changes, or comment", "status": None}}
    return await _run("submit_pull_request_review", provider, repo, pull_request_id, raw, event=event, body=body)


def http_main() -> None:
    """Run the Streamable HTTP MCP server on configured host and port.

    Returns:
        ``None`` after the server stops.

    Examples:
        Input: ``SCM_HOST=127.0.0.1, SCM_PORT=8000``.
        Output: The MCP Streamable HTTP transport serves registered tools.
    """
    logging.basicConfig(level=os.getenv("SCM_LOG_LEVEL", "INFO"), filters=[RedactFilter()])
    mcp.run(transport="streamable-http")


def stdio_main() -> None:
    """Run the stdio MCP server for local MCP clients.

    Returns:
        ``None`` after the server stops.

    Examples:
        Input: An MCP client connected to the process stdin/stdout streams.
        Output: Registered tools are served over the stdio transport.
    """
    mcp.run(transport="stdio")
