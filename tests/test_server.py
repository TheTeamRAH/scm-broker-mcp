import base64
import httpx
from scm_broker_mcp.main import mcp
from scm_broker_mcp.providers import GitHubAdapter


def test_all_fourteen_tools_are_registered():
    names = {tool.name for tool in mcp._tool_manager.list_tools()}
    assert len(names) == 14
    assert "merge_pull_request" in names


async def test_github_adapter_paginates_and_authenticates(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "token-value")
    seen = {}
    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json={"values": [{"number": 3, "title": "T", "state": "open"}], "next": "https://next"})
    adapter = GitHubAdapter(httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    payload = await adapter.call("list_pull_requests", "o/r", page=2, per_page=10)
    assert payload["values"][0]["number"] == 3
    assert seen["auth"] == "Bearer token-value"


def test_bitbucket_basic_auth_is_not_a_returned_credential(monkeypatch):
    monkeypatch.setenv("BITBUCKET_EMAIL", "a@example.com")
    monkeypatch.setenv("BITBUCKET_API_TOKEN", "token-value")
    adapter = __import__("scm_broker_mcp.providers", fromlist=["BitbucketAdapter"]).BitbucketAdapter()
    header = adapter._headers()["Authorization"]
    assert header.startswith("Basic ")
    assert "token-value" not in str({"items": []})
