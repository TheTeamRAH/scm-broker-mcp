"""Provider-neutral pull-request service and boundary validation."""

from typing import Any

from .errors import BrokerError
from .models import normalize_page, normalize_pull_request, normalize_write
from .providers import BitbucketAdapter, GitHubAdapter

_LIST_OPS = {"list_repositories", "list_pull_requests", "list_pull_request_commits", "list_pull_request_comments", "list_pull_request_reviews"}


class BrokerService:
    """Dispatch explicitly validated MCP operations to provider adapters."""

    def __init__(self, adapters: dict[str, Any] | None = None) -> None:
        self.adapters = adapters or {"github": GitHubAdapter(), "bitbucket": BitbucketAdapter()}

    def adapter(self, provider: str) -> Any:
        """Return an adapter or a structured validation error."""
        if provider not in self.adapters:
            raise BrokerError("invalid_provider", "provider must be 'github' or 'bitbucket'")
        return self.adapters[provider]

    async def execute(self, operation: str, provider: str, repo: str | None = None, pr: str | None = None, raw: bool = False, **kwargs: Any) -> Any:
        """Validate operation arguments, invoke the provider, and normalize output."""
        if operation != "list_repositories" and (not repo or "/" not in repo):
            raise BrokerError("invalid_repository", "repo must be 'owner/name' or 'workspace/slug'")
        if operation not in {"list_repositories", "list_pull_requests", "create_pull_request"} and not pr:
            raise BrokerError("missing_argument", "pull_request_id is required for this operation")
        if operation == "create_pull_request":
            if not kwargs.get("title") or not kwargs.get("source_branch") or not kwargs.get("target_branch"):
                raise BrokerError("missing_argument", "title, source_branch, and target_branch are required")
        if operation == "add_pull_request_comment" and not kwargs.get("body"):
            raise BrokerError("missing_argument", "body is required")
        page, page_size = kwargs.get("page", 1), kwargs.get("page_size", 30)
        if not isinstance(page, int) or page < 1 or not isinstance(page_size, int) or not 1 <= page_size <= 100:
            raise BrokerError("invalid_argument", "page must be >= 1 and page_size must be between 1 and 100")
        payload = await self.adapter(provider).call(operation, repo, pr, **kwargs)
        if operation in _LIST_OPS:
            return normalize_page(payload, page=page, page_size=page_size, include_raw=raw)
        if operation == "get_pull_request":
            return normalize_pull_request(payload, provider, raw)
        if operation == "get_pull_request_diff":
            return {"diff": payload if isinstance(payload, str) else payload.get("diff", ""), "raw": payload if raw and isinstance(payload, dict) else None}
        return normalize_write(payload, provider, raw)
