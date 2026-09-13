import pytest

from scm_broker_mcp.auth import Credentials, load_credentials
from scm_broker_mcp.errors import BrokerError
from scm_broker_mcp.models import normalize_pull_request


def test_github_credentials_are_loaded_without_exposing_token(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "secret-token")
    credentials = load_credentials("github")
    assert credentials == Credentials(token="secret-token")
    assert "secret-token" not in repr(credentials)


def test_missing_bitbucket_credentials_is_structured(monkeypatch):
    monkeypatch.delenv("BITBUCKET_EMAIL", raising=False)
    monkeypatch.delenv("BITBUCKET_API_TOKEN", raising=False)
    with pytest.raises(BrokerError) as exc:
        load_credentials("bitbucket")
    assert exc.value.code == "missing_credentials"
    assert "BITBUCKET" in exc.value.message


def test_normalization_produces_provider_neutral_fields():
    result = normalize_pull_request({"number": 7, "title": "Fix", "state": "open", "html_url": "https://x/7"}, "github")
    assert result == {"id": "7", "title": "Fix", "state": "open", "url": "https://x/7", "raw": None}
