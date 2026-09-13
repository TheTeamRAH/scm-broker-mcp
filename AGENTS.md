# Repository Purpose

This repository provides a Python MCP server that exposes provider-neutral pull-request tools for GitHub and Bitbucket Cloud.

## Development Flow

- Use `uv` for environments, dependency management, locking, testing, and builds.
- Keep provider credentials in environment variables or secret injection; never commit or print them.
- Use focused feature branches for implementation.
- Use test-driven development for behavior changes.
- Validate with `uv run pytest`, `uv build`, and `git diff --check`.
- The server must support network-capable MCP clients through the official Python MCP SDK and Streamable HTTP.

## Documentation

Feature specifications live under `docs/features/`. Use YAML frontmatter with `type`, `title`, `description`, `tags`, and `sources`.
