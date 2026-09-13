"""Provider-neutral pull-request service and boundary validation.

Examples:
    Input: provider-neutral operation arguments.
    Output: a normalized result mapping or safe error.
"""

from typing import Any

from .errors import BrokerError
from .models import normalize_page, normalize_pull_request, normalize_write
from .providers import BitbucketAdapter, GitHubAdapter

_LIST_OPS = {"list_repositories", "list_pull_requests", "list_pull_request_commits", "list_pull_request_comments", "list_pull_request_reviews"}


class BrokerService:
    """Dispatch validated MCP operations to provider adapters.

    Args:
        adapters: Optional provider-to-adapter mapping, useful for mocked tests.

    Examples:
        Input: ``BrokerService(adapters={"github": fake_adapter})``.
        Output: A service whose ``execute`` result uses provider-neutral fields.
    """

    def __init__(self, adapters: dict[str, Any] | None = None) -> None:
        """Create the service and default GitHub and Bitbucket adapters.

        Args:
            adapters: Optional injected adapter mapping.

        Examples:
            Input: ``adapters=None``.
            Output: ``service.adapters`` contains ``"github"`` and ``"bitbucket"``.
        """
        self.adapters = adapters or {"github": GitHubAdapter(), "bitbucket": BitbucketAdapter()}

    def adapter(self, provider: str) -> Any:
        """Return an adapter for a supported provider.

        Args:
            provider: ``"github"`` or ``"bitbucket"``.

        Returns:
            The configured provider adapter.

        Raises:
            BrokerError: If the provider is not configured.

        Examples:
            Input: ``provider="github"``.
            Output: The configured ``GitHubAdapter`` instance.
        """
        if provider not in self.adapters:
            raise BrokerError("invalid_provider", "provider must be 'github' or 'bitbucket'")
        return self.adapters[provider]

    async def execute(self, operation: str, provider: str, repo: str | None = None, pr: str | None = None, raw: bool = False, **kwargs: Any) -> Any:
        """Validate arguments, invoke an adapter, and normalize its output.

        Args:
            operation: MCP operation name.
            provider: Provider key.
            repo: Repository identity, when required.
            pr: Pull-request identifier, when required.
            raw: Include provider payloads in normalized results.
            **kwargs: Operation-specific input and pagination fields.

        Returns:
            A normalized mapping shaped as a page, pull request, diff, or write
            result depending on ``operation``.

        Raises:
            BrokerError: If required arguments or pagination are invalid.

        Examples:
            Input: ``execute("list_pull_requests", "github", "o/r", page=1)``.
            Output: ``{"items": [...], "page": 1, "page_size": 30, "has_more": False}``.
        """
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
