# scm-broker-mcp

A provider-neutral MCP server for pull-request workflows on GitHub and Bitbucket Cloud. It uses the official Python MCP SDK and supports Streamable HTTP plus stdio.

## Getting started

```bash
uv sync --dev
export GITHUB_TOKEN='…'                         # only if using GitHub
export BITBUCKET_EMAIL='you@example.com'         # only if using Bitbucket
export BITBUCKET_API_TOKEN='…'
uv run scm-broker-mcp-http                         # http://127.0.0.1:8000/mcp
# or: uv run scm-broker-mcp-stdio
```

The fourteen tools accept `provider` (`github` or `bitbucket`), `repo` (`owner/name` or `workspace/slug`), and operation-specific fields. Results have stable `id`, `state`, `url`, pagination, and optional `raw` fields. Credentials are never tool arguments or logs. Configure authentication at a reverse proxy before exposing the HTTP endpoint beyond localhost.

## Tools

`list_repositories`, `list_pull_requests`, `get_pull_request`, `get_pull_request_diff`, `list_pull_request_commits`, `create_pull_request`, `update_pull_request`, `update_pull_request_reviewers`, `close_pull_request`, `merge_pull_request`, `add_pull_request_comment`, `list_pull_request_comments`, `list_pull_request_reviews`, and `submit_pull_request_review`.

Bitbucket Cloud does not provide the same reviewer-update and review-submission semantics as GitHub; unsupported capabilities return structured `unsupported_operation` errors. Provider permissions and branch rules still apply.

## Container deployment

Build from source without secrets:

```dockerfile
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app
COPY . .
RUN uv sync --no-dev && useradd --uid 10001 --system broker
USER 10001
ENTRYPOINT ["uv", "run", "--no-dev", "scm-broker-mcp-http"]
```

Inject credentials at runtime, never into the image, source tree, files, URLs, or command line. Run as a dedicated non-root UID with a read-only root filesystem and dropped capabilities. Keep untrusted agents away from the server container's filesystem, process namespace, and secret-bearing environment. This assumes the deployment platform enforces container separation; environment credentials do not protect against a privileged agent sharing the container or host. Bind to localhost by default and use an authenticated reverse proxy for remote access.

## Recent Features

| Date | Purpose | Spec | Author |
| --- | --- | --- | --- |
| 2026-09-13-17-39 | Scoped pull-request MCP server | [Scoped pull-request MCP server](docs/features/2026-09-13-17-39-scoped-pull-request-mcp-server.md) | whose-footprints-are-these |

## Repo Structure

```text
src/scm_broker_mcp/  # server, service, schemas, provider adapters
tests/                # mocked contract and protocol tests
docs/features/        # approved feature specifications
```

## Development

```bash
uv run pytest
uv build
uv lock --check
git diff --check
```
## Contributing

This is an AI-first repository. Read [AGENTS.md](AGENTS.md), use a reviewed feature specification, work on a focused branch, and follow test-driven development. Do not commit credentials or generated environments.
