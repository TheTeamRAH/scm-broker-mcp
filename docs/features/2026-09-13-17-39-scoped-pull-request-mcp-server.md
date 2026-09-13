---
type: feature
status: completed
title: Scoped pull-request MCP server
description: Build and publish a Python MCP server exposing provider-neutral GitHub and Bitbucket Cloud pull-request tools over network-capable MCP transport.
tags:
  - mcp
  - github
  - bitbucket
  - pull-requests
  - python
  - uv
sources:
  - title: MCP Python SDK
    url: https://py.sdk.modelcontextprotocol.io/
  - title: MCP transport specification
    url: https://modelcontextprotocol.io/specification/2026-07-28/basic/transports
  - title: GitHub REST pull requests API
    url: https://docs.github.com/en/rest/pulls/pulls
  - title: Bitbucket Cloud pull requests API
    url: https://developer.atlassian.com/cloud/bitbucket/rest/api-group-pullrequests/
---

# Scoped pull-request MCP server

## Context

Agents need a single MCP interface for pull-request work across GitHub and Bitbucket Cloud. The existing Semaphore CLI establishes the repository convention: Python packaging through `pyproject.toml`, reproducible `uv.lock`, test-first development, and installation/deployment through `uv`.

The server must be usable by agents running locally and by agents connecting to a deployed network endpoint. The official MCP Python SDK supports standard transports; Streamable HTTP is the network transport for this feature, with stdio retained as a local development option.

Recent GitHub and Bitbucket PR workflows used listing and inspecting PRs, opening and updating them, closing them, reading and posting comments, reviewing diffs, approving, and merging. The initial action set therefore includes the complete basic lifecycle, review context, and review decision operations.

## Goal

Publish a public repository named `TheTeamRAH/scm-broker-mcp` containing an independently usable Python MCP server that agents can configure with provider API credentials and use against GitHub or Bitbucket Cloud.

## Scope

### MCP tools

Each tool accepts an explicit `provider` (`github` or `bitbucket`) and provider-specific repository identity. Tool results use stable provider-neutral fields while retaining a safe `raw` provider payload only when explicitly requested by the caller. Pagination is supported using provider-neutral `page`/`page_size` or continuation tokens as appropriate.

Required tools:

- `list_repositories`
- `list_pull_requests`
- `get_pull_request`
- `get_pull_request_diff`
- `list_pull_request_commits`
- `create_pull_request`
- `update_pull_request`
- `update_pull_request_reviewers`
- `close_pull_request`
- `merge_pull_request`
- `add_pull_request_comment`
- `list_pull_request_comments`
- `list_pull_request_reviews`
- `submit_pull_request_review`

`submit_pull_request_review` supports at least `approve`, `request_changes`, and review `comment`, subject to provider capability and permissions. `merge_pull_request` accepts an explicit merge method where the provider supports it and returns the resulting state.

### Provider credentials

- GitHub: `GITHUB_TOKEN`
- Bitbucket Cloud: `BITBUCKET_EMAIL` and `BITBUCKET_API_TOKEN`

Credentials are read only from the process environment or an equivalent secret-injection mechanism. They are never accepted as tool arguments, written to ordinary application files, placed in URLs, logged, or returned in tool results. Missing credentials produce clear, non-sensitive errors.

The initial implementation uses environment mode only. The documented variables are `GITHUB_TOKEN`, `BITBUCKET_EMAIL`, and `BITBUCKET_API_TOKEN`. The container runtime supplies these values; the image contains no secrets. The server never copies credentials into tool results, logs, command-line arguments, or ordinary application files.

The container is the isolation boundary: agents are kept away from the server container's filesystem, process namespace, and secret-bearing environment. The recommended container runs the server as a dedicated non-root UID with a read-only root filesystem, dropped capabilities, and no shell or debugging tools. This design assumes the deployment platform enforces separation between the agent and server containers; it does not attempt to defend against a privileged agent that can inspect the server container or host.

The credential source remains behind a small provider credential interface so a later Vault, cloud secret-manager, or Unix-socket broker integration does not change MCP tools. No broker or secret-file mode is required for the initial implementation.

### Transport and runtime

- Official Python MCP SDK.
- Streamable HTTP endpoint for deployed/network use.
- Stdio transport for local MCP hosts and development.
- Configuration through environment variables for bind host, port, and log level, with safe defaults documented in the README.
- `uv sync`, `uv run`, `uv build`, and `uv tool install` are supported workflows.
- Container startup documentation covering runtime environment secrets, dedicated UID permissions, read-only filesystems, and the separate-container requirement for untrusted agents.

### Repository contents

- `pyproject.toml` with package metadata and console entry point.
- `uv.lock` committed for reproducibility.
- Typed provider clients with isolated GitHub and Bitbucket Cloud adapters.
- Provider-neutral schemas and explicit capability/error handling.
- Unit tests using mocked HTTP transports; no live credentials in tests.
- README with installation, server startup, MCP client configuration, credential setup, tool examples, provider limitations, and security notes.

## Requirements

1. The server starts through `uv run` and exposes the Streamable HTTP MCP endpoint without requiring a source checkout at runtime.
2. The stdio transport remains available for local MCP clients.
3. All listed tools validate required arguments before making an HTTP request.
4. GitHub requests use bearer/token authentication and Bitbucket requests use email/API-token authentication without credential leakage.
5. Provider-specific responses are normalized consistently for list, detail, diff, comments, commits, reviewers, reviews, and state-changing operations.
6. List operations follow provider pagination and expose whether more results remain.
7. Write operations return the provider identifier, resulting state, and web URL when available.
8. Provider capability differences are reported as structured, actionable errors rather than silently ignored.
9. Network failures, authentication failures, rate limits, malformed responses, and unsupported operations have stable non-secret error types/messages.
10. Tests cover every tool's happy path, validation failures, authentication configuration, pagination, provider error mapping, and write-result normalization.
11. `uv build` produces an installable distribution, and the documented `uv tool install` path works from the built artifact.
12. No tokens, authorization headers, live repository data, or generated virtual environments are committed.
13. Container deployment does not require secrets in the image, source tree, ordinary application files, or command-line arguments.
14. Tests cover environment loading, missing credentials, and redaction guarantees.
15. Documentation clearly states that the deployment platform must keep agents away from the server container's filesystem, process namespace, and secret-bearing environment.

## Acceptance criteria

- Public repository URL is `https://github.com/TheTeamRAH/scm-broker-mcp`.
- A clean checkout can install and run the server with `uv` using only documented environment configuration.
- A network MCP client can discover and invoke the tools through Streamable HTTP.
- Mocked tests pass for all fourteen tools on both providers where supported, with explicit tests for capability differences.
- `uv lock --check`, `uv run pytest`, `uv build`, and `git diff --check` pass.
- README examples are sufficient for configuring an agent with GitHub and Bitbucket credentials without exposing secrets.

## Constraints

- Python remains the implementation language.
- Do not add provider-specific credentials to source, fixtures, command arguments, or logs.
- Do not use Docker as a required deployment mechanism; `uv` is the deployment/install path.
- Do not claim live provider compatibility without mocked contract tests and a successful local protocol smoke test.
- Keep the initial interface focused on pull requests; issues, repository administration, CI, branch writes, and arbitrary file writes are out of scope.

## Implementation notes

Use small provider adapters behind a shared service layer. Keep transport, schema, authentication, HTTP, normalization, and error mapping separable so provider behavior can be tested independently. Prefer the SDK's current server API and Streamable HTTP transport rather than inventing an HTTP wrapper around MCP.

The initial implementation may use one server process with both stdio and Streamable HTTP entry points. The network endpoint must not echo request headers or environment values, and logging must redact authorization material by construction.

## Risks and mitigations

- **Provider semantic differences:** model states and review capabilities explicitly; test unsupported operations.
- **API drift:** isolate endpoint paths and response normalization in adapters; pin compatible dependencies through `uv.lock`.
- **Credential leakage:** environment-only credentials, redacted logging, and tests that assert headers are not returned.
- **Network exposure:** bind to localhost by default and document reverse-proxy/authentication requirements for remote exposure.
- **Container co-tenancy:** environment credentials are safe only when the deployment platform keeps agents away from the server container and its process namespace.

## Validation

From a clean checkout:

```bash
uv sync --dev
uv run pytest
uv build
uv lock --check
git diff --check
```

Run a local protocol smoke test using the stdio entry point and an HTTP health/protocol smoke test against the Streamable HTTP entry point. Use mocked provider transports for functional tests; live provider tests are optional and must be opt-in, never required for the default suite.

Container validation must also verify that the image contains no credential values, the server starts with runtime-provided environment variables, and logs/tool results contain no credential material. The deployment documentation must not claim isolation against a privileged agent sharing the server container or host.

## Amendments

- Use environment-only credentials, with the deployment platform keeping agents away from the server container's filesystem, process namespace, and secret-bearing environment. Defer secret-file and external credential-broker modes.

## Lifecycle

Status is `proposed` pending human review. Implementation must not begin until the specification is approved.
