"""FastMCP transports and operation-specific tool definitions."""

import logging
import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from .errors import BrokerError
from .service import BrokerService


class RedactFilter(logging.Filter):
    """Prevent common credential material from entering logs."""

    def filter(self, record: logging.LogRecord) -> bool:
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
    """Execute a tool and convert expected errors to structured results."""
    try:
        return await service.execute(operation, provider, repo, pull_request_id, raw, **kwargs)
    except BrokerError as exc:
        return {"error": {"type": exc.code, "message": exc.message, "status": exc.status}}


@mcp.tool()
async def list_repositories(provider: str, workspace: str | None = None, page: int = 1, page_size: int = 30, raw: bool = False) -> dict[str, Any]:
    """List repositories visible to the authenticated provider account."""
    return await _run("list_repositories", provider, workspace, raw=raw, page=page, page_size=page_size)


@mcp.tool()
async def list_pull_requests(provider: str, repo: str, state: str = "open", page: int = 1, page_size: int = 30, raw: bool = False) -> dict[str, Any]:
    """List pull requests in a repository."""
    return await _run("list_pull_requests", provider, repo, raw=raw, state=state, page=page, page_size=page_size)


@mcp.tool()
async def get_pull_request(provider: str, repo: str, pull_request_id: str, raw: bool = False) -> dict[str, Any]:
    """Get one pull request."""
    return await _run("get_pull_request", provider, repo, pull_request_id, raw=raw)


@mcp.tool()
async def get_pull_request_diff(provider: str, repo: str, pull_request_id: str) -> dict[str, Any]:
    """Get a pull request unified diff."""
    return await _run("get_pull_request_diff", provider, repo, pull_request_id)


@mcp.tool()
async def list_pull_request_commits(provider: str, repo: str, pull_request_id: str, page: int = 1, page_size: int = 30, raw: bool = False) -> dict[str, Any]:
    """List commits associated with a pull request."""
    return await _run("list_pull_request_commits", provider, repo, pull_request_id, raw, page=page, page_size=page_size)


@mcp.tool()
async def create_pull_request(provider: str, repo: str, title: str, source_branch: str, target_branch: str, description: str = "", raw: bool = False) -> dict[str, Any]:
    """Create a pull request from source_branch into target_branch."""
    return await _run("create_pull_request", provider, repo, raw=raw, title=title, source_branch=source_branch, target_branch=target_branch, description=description)


@mcp.tool()
async def update_pull_request(provider: str, repo: str, pull_request_id: str, title: str | None = None, description: str | None = None, raw: bool = False) -> dict[str, Any]:
    """Update a pull request title or description."""
    return await _run("update_pull_request", provider, repo, pull_request_id, raw, title=title, description=description)


@mcp.tool()
async def update_pull_request_reviewers(provider: str, repo: str, pull_request_id: str, reviewers: list[str]) -> dict[str, Any]:
    """Request reviewers, when supported by the provider."""
    return await _run("update_pull_request_reviewers", provider, repo, pull_request_id, reviewers=reviewers)


@mcp.tool()
async def close_pull_request(provider: str, repo: str, pull_request_id: str, raw: bool = False) -> dict[str, Any]:
    """Close or decline a pull request."""
    return await _run("close_pull_request", provider, repo, pull_request_id, raw=raw)


@mcp.tool()
async def merge_pull_request(provider: str, repo: str, pull_request_id: str, merge_method: str = "merge", raw: bool = False) -> dict[str, Any]:
    """Merge a pull request using an explicit provider-supported method."""
    if merge_method not in {"merge", "squash", "rebase"}:
        return {"error": {"type": "invalid_argument", "message": "merge_method must be merge, squash, or rebase", "status": None}}
    return await _run("merge_pull_request", provider, repo, pull_request_id, raw, merge_method=merge_method)


@mcp.tool()
async def add_pull_request_comment(provider: str, repo: str, pull_request_id: str, body: str, raw: bool = False) -> dict[str, Any]:
    """Add a comment to a pull request."""
    return await _run("add_pull_request_comment", provider, repo, pull_request_id, raw, body=body)


@mcp.tool()
async def list_pull_request_comments(provider: str, repo: str, pull_request_id: str, page: int = 1, page_size: int = 30, raw: bool = False) -> dict[str, Any]:
    """List pull request comments."""
    return await _run("list_pull_request_comments", provider, repo, pull_request_id, raw, page=page, page_size=page_size)


@mcp.tool()
async def list_pull_request_reviews(provider: str, repo: str, pull_request_id: str, page: int = 1, page_size: int = 30, raw: bool = False) -> dict[str, Any]:
    """List pull request reviews."""
    return await _run("list_pull_request_reviews", provider, repo, pull_request_id, raw, page=page, page_size=page_size)


@mcp.tool()
async def submit_pull_request_review(provider: str, repo: str, pull_request_id: str, event: str, body: str = "", raw: bool = False) -> dict[str, Any]:
    """Submit an approve, request_changes, or comment review."""
    if event not in {"approve", "request_changes", "comment"}:
        return {"error": {"type": "invalid_argument", "message": "event must be approve, request_changes, or comment", "status": None}}
    return await _run("submit_pull_request_review", provider, repo, pull_request_id, raw, event=event, body=body)


def http_main() -> None:
    """Run the Streamable HTTP MCP server."""
    logging.basicConfig(level=os.getenv("SCM_LOG_LEVEL", "INFO"), filters=[RedactFilter()])
    mcp.run(transport="streamable-http")


def stdio_main() -> None:
    """Run the stdio MCP server."""
    mcp.run(transport="stdio")
