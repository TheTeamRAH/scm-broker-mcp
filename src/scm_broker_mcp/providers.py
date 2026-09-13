"""Typed provider adapters backed by httpx."""

import base64
from typing import Any

import httpx

from .auth import load_credentials
from .errors import BrokerError, map_http_error


class ProviderAdapter:
    """Common REST adapter contract for supported providers."""

    name = ""
    base_url = ""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self.client = client or httpx.AsyncClient(timeout=30)

    def _headers(self, *, accept: str | None = None) -> dict[str, str]:
        credentials = load_credentials(self.name)
        if self.name == "github":
            return {"Authorization": f"Bearer {credentials.token}", "Accept": accept or "application/vnd.github+json"}
        encoded = base64.b64encode(f"{credentials.email}:{credentials.token}".encode()).decode()
        return {"Authorization": f"Basic {encoded}", "Accept": accept or "application/json"}

    async def request(self, method: str, path: str, *, params: dict[str, Any] | None = None, json: Any = None, accept: str | None = None) -> Any:
        """Perform an authenticated request and map unsafe provider errors."""
        try:
            response = await self.client.request(method, self.base_url + path, headers=self._headers(accept=accept), params=params, json=json)
        except httpx.HTTPError as exc:
            raise BrokerError("network_error", "Provider network request failed") from exc
        if response.status_code >= 400:
            raise map_http_error(response.status_code)
        if not response.content:
            return {}
        try:
            return response.json()
        except ValueError as exc:
            if accept and "diff" in accept:
                return response.text
            raise BrokerError("malformed_response", "Provider returned malformed JSON") from exc


class GitHubAdapter(ProviderAdapter):
    """GitHub REST pull-request adapter."""

    name, base_url = "github", "https://api.github.com"

    async def call(self, operation: str, repo: str | None = None, pr: str | None = None, **kwargs: Any) -> Any:
        """Execute one operation using GitHub's REST contract."""
        if operation == "list_repositories":
            return await self.request("GET", "/user/repos", params={"page": kwargs.get("page", 1), "per_page": kwargs.get("page_size", 30)})
        if not repo:
            raise BrokerError("invalid_repository", "repo is required")
        root = f"/repos/{repo}"
        paths = {
            "list_pull_requests": ("GET", f"{root}/pulls"), "get_pull_request": ("GET", f"{root}/pulls/{pr}"),
            "get_pull_request_diff": ("GET", f"{root}/pulls/{pr}"), "list_pull_request_commits": ("GET", f"{root}/pulls/{pr}/commits"),
            "create_pull_request": ("POST", f"{root}/pulls"), "update_pull_request": ("PATCH", f"{root}/pulls/{pr}"),
            "update_pull_request_reviewers": ("POST", f"{root}/pulls/{pr}/requested_reviewers"), "close_pull_request": ("PATCH", f"{root}/pulls/{pr}"),
            "merge_pull_request": ("PUT", f"{root}/pulls/{pr}/merge"), "add_pull_request_comment": ("POST", f"{root}/issues/{pr}/comments"),
            "list_pull_request_comments": ("GET", f"{root}/issues/{pr}/comments"), "list_pull_request_reviews": ("GET", f"{root}/pulls/{pr}/reviews"),
            "submit_pull_request_review": ("POST", f"{root}/pulls/{pr}/reviews"),
        }
        if operation not in paths:
            raise BrokerError("unsupported_operation", f"GitHub does not support {operation}")
        method, path = paths[operation]
        params = {"page": kwargs.get("page", 1), "per_page": kwargs.get("page_size", 30)} if method == "GET" else None
        payload = {key: value for key, value in kwargs.items() if value is not None}
        if operation == "create_pull_request":
            payload = {"title": kwargs["title"], "head": kwargs["source_branch"], "base": kwargs["target_branch"], "body": kwargs.get("description", "")}
        elif operation == "update_pull_request":
            payload = {key: kwargs[key] for key in ("title", "description") if kwargs.get(key) is not None}
            if "description" in payload:
                payload["body"] = payload.pop("description")
        elif operation == "update_pull_request_reviewers":
            payload = {"reviewers": kwargs["reviewers"]}
        elif operation == "close_pull_request":
            payload = {"state": "closed"}
        elif operation == "merge_pull_request":
            payload = {"merge_method": kwargs["merge_method"]}
        elif operation == "add_pull_request_comment":
            payload = {"body": kwargs["body"]}
        elif operation == "submit_pull_request_review":
            payload = {"event": kwargs["event"].upper(), "body": kwargs.get("body", "")}
        if operation == "get_pull_request_diff": return await self.request(method, path, accept="application/vnd.github.diff")
        return await self.request(method, path, params=params, json=payload if method != "GET" else None)


class BitbucketAdapter(ProviderAdapter):
    """Bitbucket Cloud REST pull-request adapter."""

    name, base_url = "bitbucket", "https://api.bitbucket.org/2.0"

    async def call(self, operation: str, repo: str | None = None, pr: str | None = None, **kwargs: Any) -> Any:
        """Execute one operation using Bitbucket Cloud's REST contract."""
        if operation == "list_repositories":
            path = f"/repositories/{repo}" if repo else "/repositories"
            return await self.request("GET", path, params={"page": kwargs.get("page", 1), "pagelen": kwargs.get("page_size", 30)})
        if operation == "update_pull_request_reviewers" or (operation == "submit_pull_request_review" and kwargs.get("event") != "approve"):
            raise BrokerError("unsupported_operation", "Bitbucket Cloud does not support this review operation")
        if not repo:
            raise BrokerError("invalid_repository", "repo is required")
        root = f"/repositories/{repo}"
        paths = {
            "list_pull_requests": ("GET", f"{root}/pullrequests"), "get_pull_request": ("GET", f"{root}/pullrequests/{pr}"),
            "get_pull_request_diff": ("GET", f"{root}/pullrequests/{pr}/diff"), "list_pull_request_commits": ("GET", f"{root}/pullrequests/{pr}/commits"),
            "create_pull_request": ("POST", f"{root}/pullrequests"), "update_pull_request": ("PUT", f"{root}/pullrequests/{pr}"),
            "close_pull_request": ("PUT", f"{root}/pullrequests/{pr}"), "merge_pull_request": ("POST", f"{root}/pullrequests/{pr}/merge"),
            "add_pull_request_comment": ("POST", f"{root}/pullrequests/{pr}/comments"), "list_pull_request_comments": ("GET", f"{root}/pullrequests/{pr}/comments"),
            "list_pull_request_reviews": ("GET", f"{root}/pullrequests/{pr}/activity"), "submit_pull_request_review": ("POST", f"{root}/pullrequests/{pr}/approve"),
        }
        method, path = paths[operation]
        params = {"page": kwargs.get("page", 1), "pagelen": kwargs.get("page_size", 30)} if method == "GET" else None
        payload = {key: value for key, value in kwargs.items() if value is not None}
        if operation == "create_pull_request":
            payload = {"title": kwargs["title"], "description": kwargs.get("description", ""), "source": {"branch": {"name": kwargs["source_branch"]}}, "destination": {"branch": {"name": kwargs["target_branch"]}}}
        elif operation == "update_pull_request":
            payload = {key: kwargs[key] for key in ("title", "description") if kwargs.get(key) is not None}
        elif operation == "merge_pull_request":
            strategies = {"merge": "merge_commit", "squash": "squash", "rebase": "fast_forward"}
            payload = {"merge_strategy": strategies[kwargs["merge_method"]]}
        elif operation == "close_pull_request":
            payload = {"state": "DECLINED"}
        elif operation == "add_pull_request_comment":
            payload = {"content": {"raw": kwargs["body"]}}
        if operation == "submit_pull_request_review":
            payload = None
        return await self.request(method, path, params=params, json=payload if method != "GET" else None)
