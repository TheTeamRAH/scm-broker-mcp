# scm-broker-mcp

A Python MCP server exposing provider-neutral pull-request workflows for GitHub and Bitbucket Cloud.

## Repo Structure

```text
.
├── AGENTS.md
├── docs/
│   └── features/
│       ├── README.md
│       └── 2026-09-13-17-39-scoped-pull-request-mcp-server.md
├── README.md
└── .gitignore
```

Implementation is not yet recorded; this repository currently contains the proposed feature specification and project guidance.

## Getting Started

Implementation has not started. After approval, the project will use `uv` for development, testing, building, and installation. Provider credentials will be configured through secret injection using `GITHUB_TOKEN`, `BITBUCKET_EMAIL`, and `BITBUCKET_API_TOKEN`; credentials must never be committed or logged.

### Container deployment

The image contains no secrets. The container runtime supplies `GITHUB_TOKEN`, `BITBUCKET_EMAIL`, and `BITBUCKET_API_TOKEN` as environment variables. Run the server as a dedicated non-root UID with a read-only root filesystem and dropped capabilities. Keep agents away from the server container's filesystem, process namespace, and environment; allow access only through authenticated MCP networking. Environment variables cannot protect a secret from a privileged agent sharing the container.

## Recent Features

| Date | Purpose | Spec | Author |
| --- | --- | --- | --- |

No implemented features are recorded yet.

See [all feature specifications](docs/features/README.md).

## Contributing

This is an AI-first development repository. Point your agent or model at [AGENTS.md](AGENTS.md) before contributing.

- Create and have a complete feature specification reviewed before implementation.
- Use focused feature branches and test-driven development for code changes.
- Use `uv` for Python environments, dependencies, tests, and builds.
- Follow the documentation structure, timestamp rules, and OKF requirements in `AGENTS.md`.
- Consult discovery documentation before related work and keep reusable lessons current.
