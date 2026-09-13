---
type: feature
status: proposed
title: Agentic container deployment for SCM broker
description: Package scm-broker-mcp as a secret-free, non-root Docker service that can be consumed privately by the agentic stack.
tags:
  - docker
  - docker-compose
  - mcp
  - agentic
  - github
  - bitbucket
sources:
  - title: Repository implementation specification
    url: ./2026-09-13-17-39-scoped-pull-request-mcp-server.md
  - title: Repository guidance
    url: ../../AGENTS.md
  - title: Model Context Protocol transports
    url: https://modelcontextprotocol.io/specification/2025-06-18/basic/transports
---

# Agentic container deployment for SCM broker

## Context

`TheTeamRAH/scm-broker-mcp` already contains a provider-neutral Python MCP server with Streamable HTTP and stdio entry points. The server reads GitHub and Bitbucket credentials from runtime environment variables and defaults to localhost port 8000. The requested deployment must be usable by the agentic execution environment without exposing an independent host service.

## Goal

Provide a reproducible container image and Compose definition for the broker. The definition must be suitable for inclusion in the private `agentic` stack, where agents can reach the broker over the Compose network but no host port is published.

## Scope

- Add a repository-root `Dockerfile` using a pinned Python runtime and `uv` to install the locked application without development dependencies.
- Add a repository-root `docker-compose.yml` defining one `scm-broker` service for standalone validation and reuse by the agentic stack.
- Add an untracked `.env.example` containing non-secret bind and port defaults only.
- Document runtime secret injection, the internal service URL, health/protocol smoke testing, and the separation boundary between agent and broker containers.
- Keep the service on the private Compose network with no published ports, host networking, privileged mode, Docker socket, or credentials in the image.

## Out of scope

- Live deployment, stack startup, reverse proxy, firewall changes, or host port allocation.
- Secret values, Vault implementation, provider login, or agent model configuration.
- Changes to the Python tool interface or provider APIs.
- Making the broker available to unrelated Compose stacks.

## Requirements

1. The Dockerfile must install the package from the repository and `uv.lock`, run as a dedicated non-root user, and start `scm-broker-mcp-http`.
2. The image must not contain `GITHUB_TOKEN`, `BITBUCKET_EMAIL`, or `BITBUCKET_API_TOKEN`; Compose must receive those values only through an external runtime env file or equivalent secret injection.
3. The Compose service must use a fixed reviewable image tag, `restart: unless-stopped`, an explicit `container_name` consistent with repository conventions, and an internal-only binding of `8000`.
4. The Compose definition must publish no ports and must not add privileged access, capabilities, devices, host networking, or a Docker socket.
5. The broker must be reachable from a client on the same Compose network as `http://scm-broker:8000/mcp`; the README must state that this URL is private to the stack.
6. The agentic stack integration must build or reference this service as a sibling service on the agentic Compose network, rather than publish a separate host endpoint or add the service to unrelated stacks.
7. The README must document `uv run pytest`, `uv build`, `uv lock --check`, `docker compose config`, and an opt-in protocol smoke test with credentials supplied from the runtime environment.

## Acceptance criteria

- `Dockerfile`, `docker-compose.yml`, and `.env.example` exist with no secret values.
- The image installs the locked application and starts the HTTP MCP entry point as non-root.
- `docker compose config` succeeds without requiring credentials or starting containers.
- Static inspection confirms no published ports, Docker socket, privileged mode, host networking, or tracked secrets.
- The private service URL and agentic-only availability are documented.
- Existing Python tests and package-build checks remain passing.

## Validation

```bash
uv lock --check
uv run pytest
uv build
docker compose config
# Only when separately authorized and runtime credentials are available:
# docker compose build
# docker compose run --rm scm-broker python -c '...protocol smoke test...'
git diff --check
```

## Risks and mitigations

- **Credential leakage:** inject credentials at runtime and test the image context for secret names and values.
- **Accidental network exposure:** omit `ports` and document the internal DNS name rather than localhost.
- **Agent co-tenancy:** keep the broker in a separate container and do not claim protection from a privileged agent with host/container inspection rights.
- **Dependency drift:** install from `uv.lock` and pin the base image or document the approved update process.

## Fresh-context readiness review

The cited repository specification and guidance identify the existing entry points, credential names, private-network boundary, required validation, and intentional non-changes. Implementation choices that do not affect the service contract—such as the exact non-root UID and minimal Python base image—remain ordinary implementation discretion.

## Lifecycle

Status is `proposed` pending review. Implementation and deployment are separate follow-on actions.
