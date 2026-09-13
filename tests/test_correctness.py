"""Focused contract tests for tool schemas and provider HTTP mappings."""

import inspect

import httpx
import pytest

from scm_broker_mcp.main import (
    add_pull_request_comment, close_pull_request, create_pull_request,
    get_pull_request, get_pull_request_diff, list_pull_request_comments,
    list_pull_request_commits, list_pull_request_reviews, list_pull_requests,
    list_repositories, merge_pull_request, submit_pull_request_review,
    update_pull_request, update_pull_request_reviewers,
)
from scm_broker_mcp.providers import BitbucketAdapter, GitHubAdapter
from scm_broker_mcp.service import BrokerService


TOOLS = [list_repositories, list_pull_requests, get_pull_request, get_pull_request_diff,
         list_pull_request_commits, create_pull_request, update_pull_request,
         update_pull_request_reviewers, close_pull_request, merge_pull_request,
         add_pull_request_comment, list_pull_request_comments,
         list_pull_request_reviews, submit_pull_request_review]


def test_tools_have_operation_specific_typed_signatures():
    signatures = {tool.__name__: inspect.signature(tool) for tool in TOOLS}
    assert all("kwargs" not in str(signature) for signature in signatures.values())
    assert signatures["list_repositories"].parameters["workspace"].default is None
    assert signatures["create_pull_request"].parameters["source_branch"].annotation is str
    assert signatures["add_pull_request_comment"].parameters["body"].annotation is str
    assert signatures["update_pull_request_reviewers"].parameters["reviewers"].annotation == list[str]


class RecordingAdapter:
    async def call(self, operation, repo=None, pr=None, **kwargs):
        self.last = (operation, repo, pr, kwargs)
        if operation in {"list_repositories", "list_pull_requests", "list_pull_request_commits", "list_pull_request_comments", "list_pull_request_reviews"}:
            return {"values": [{"id": 1}], "next": "continuation"}
        return {"id": 1, "number": 1, "state": "OPEN", "title": "x"}


@pytest.mark.parametrize("operation", [
    "list_repositories", "list_pull_requests", "get_pull_request", "get_pull_request_diff",
    "list_pull_request_commits", "create_pull_request", "update_pull_request",
    "update_pull_request_reviewers", "close_pull_request", "merge_pull_request",
    "add_pull_request_comment", "list_pull_request_comments", "list_pull_request_reviews",
    "submit_pull_request_review",
])
async def test_each_operation_has_service_contract(operation):
    adapter = RecordingAdapter()
    service = BrokerService({"github": adapter})
    args = {"page": 1, "page_size": 10}
    if operation != "list_repositories": args["repo"] = "owner/name"
    if operation not in {"list_repositories", "list_pull_requests", "create_pull_request"}: args["pr"] = "2"
    if operation == "create_pull_request": args.update(title="t", source_branch="feature", target_branch="main")
    if operation == "add_pull_request_comment": args["body"] = "hello"
    result = await service.execute(operation, args.pop("provider", "github"), **args)
    assert "error" not in result
    assert adapter.last[0] == operation


def _client(adapter, env):
    async def handler(request):
        env["method"] = request.method
        env["path"] = request.url.path
        env["json"] = request.content
        return httpx.Response(200, json={"id": 9, "number": 9, "state": "OPEN", "values": []})
    adapter.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return adapter


@pytest.mark.parametrize("provider,adapter,repo", [("github", GitHubAdapter(), "o/r"), ("bitbucket", BitbucketAdapter(), "w/r")])
async def test_representative_write_mappings(provider, adapter, repo, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setenv("BITBUCKET_EMAIL", "a@b.test")
    monkeypatch.setenv("BITBUCKET_API_TOKEN", "y")
    seen = {}
    adapter = _client(adapter, seen)
    await adapter.call("create_pull_request", repo, title="T", source_branch="feature", target_branch="main", description="D")
    assert seen["method"] == "POST"
    assert seen["path"].endswith("/pulls") or seen["path"].endswith("/pullrequests")
    await adapter.call("close_pull_request", repo, "4")
    assert seen["method"] == "PATCH" if provider == "github" else seen["method"] == "PUT"
    await adapter.call("merge_pull_request", repo, "4", merge_method="squash")
    assert seen["method"] == "PUT" if provider == "github" else seen["method"] == "POST"


@pytest.mark.parametrize("adapter,repo", [(GitHubAdapter(), None), (BitbucketAdapter(), None)])
async def test_list_repositories_does_not_require_repo(adapter, repo, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setenv("BITBUCKET_EMAIL", "a@b.test")
    monkeypatch.setenv("BITBUCKET_API_TOKEN", "y")
    seen = {}
    adapter = _client(adapter, seen)
    await adapter.call("list_repositories", repo, page=2, page_size=7)
    assert seen["method"] == "GET"
    assert seen["path"].endswith(("/user/repos", "/repositories"))


async def test_bitbucket_reviewer_update_is_structured_unsupported(monkeypatch):
    monkeypatch.setenv("BITBUCKET_EMAIL", "a@b.test")
    monkeypatch.setenv("BITBUCKET_API_TOKEN", "y")
    from scm_broker_mcp.main import _run
    result = await _run("update_pull_request_reviewers", "bitbucket", "w/r", "3", reviewers=["alice"])
    assert result["error"]["type"] == "unsupported_operation"
