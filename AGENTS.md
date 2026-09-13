# Repository Purpose

This repository provides a Python MCP server that exposes provider-neutral pull-request tools for GitHub and Bitbucket Cloud.

## Communication and Research

- Give brief, direct answers that address the request.
- Source factual statements. When research is needed, use multiple independent, relevant sources, cross-check the claims, and link the sources used. Prefer primary sources where practical.
- Be explicit when information is unknown, needs research, or needs user input. Ask clarifying questions whenever a material requirement is unclear.

## Repository Documentation

Use and maintain this structure:

```text
docs/
├── architecture/  # Architecture documentation, organized by area or technology.
├── features/      # Self-contained feature specifications.
├── decisions/     # Architecture decision records (ADRs).
├── discovery/     # Reusable lessons learned, organized by area or technology.
└── debugging/     # Debugging investigations and outcomes.
```

The `docs/` structure above defines the required documentation, development, and learning system. It is not a complete inventory of source files or directories. Keep the detailed project structure in the root README's `Repo Structure` section and do not reproduce it here.

Every Markdown documentation artifact under `docs/` must conform to Open Knowledge Format (OKF) v0.2: [OKF specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md). Normal Markdown files are OKF concept documents with YAML frontmatter containing at least `type`, `title`, `description`, `tags`, and provenance `sources` where applicable. Attribute source-specific claims with Markdown footnotes keyed to `sources` entries. Preserve unknown OKF frontmatter keys when updating documents. Use `index.md` and `log.md` only in their defined OKF roles and formats.

For timestamped documents, obtain the timestamp at creation time and never calculate it manually:

```bash
date +"%Y-%m-%d-%H-%M"
```

Use `YYYY-MM-DD-HH-MM-<purpose>.md`, with a concise lowercase-hyphenated purpose.

- `docs/architecture`: Document architecture by area or technology; no timestamp prefix.
- `docs/features`: Feature specifications; timestamp prefix required.
- `docs/decisions`: Nygard-style ADRs with `Title`, `Context`, `Decision`, `Status`, and `Consequences`; use [Michael Nygard's source](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions).
- `docs/discovery`: Reusable lessons by area or technology; consult before related work and keep current and non-duplicative.
- `docs/debugging`: Investigations and outcomes; consult `docs/discovery` first and use the timestamp prefix.

## Development Flow

1. Do not use Compound Engineering skills other than a review skill.
2. Do not run `git add` or `git commit` unless the user explicitly asks.
3. Before implementation, create a complete, self-contained feature specification in `docs/features`. Include context, goal, scope, requirements, acceptance criteria, constraints, implementation notes, risks, validation, and source links. Give a new context window, using only the specification and its cited repository sources, every fact, decision, constraint, dependency, relevant path, interface expectation, validation command or procedure, and source needed to implement, validate, and determine completion without prior conversation or unstated assumptions.
4. While drafting, resolve material ambiguity with authoritative repository evidence or focused user questions; do not invent material requirements or silently choose between materially different interpretations.
5. After drafting, perform a fresh-context readiness review and close unresolved placeholders, ambiguous references, hidden context, unsupported assumptions, missing edge cases, incomplete acceptance criteria, and unusable validation steps. Keep the specification proposed when user input is required.
6. Ask the user to review the specification. Do not implement until they ask to continue.
7. On continuation, create a focused `feature/`, `fix/`, or `explore/` branch before implementation. Immediately update the root README `Recent Features` table and exhaustive `docs/features/README.md` index, newest first, using `Date`, `Purpose`, `Spec`, and `Author`; keep at most ten root rows and use complete timestamp prefixes.
8. Use test-driven development for code: write and run a failing test first, then implement and rerun it. Prefer Python; use Bash only for simple work.
9. Implement and validate the approved specification on the branch.
10. Review changed code and documentation for clarity, maintainability, duplication, consistency, links, reusable lessons, and necessary README structure updates.
11. If work stops, perform the applicable quality and documentation review, preserve the truthful specification status, and do not declare completion.
12. Record small out-of-scope user requests during active work in `## Amendments` in the active specification before completion or handoff. Do not amend completed specifications except to correct premature completion of current work.
13. Before completion, merge current `main` into the feature branch, resolve conflicts, rerun affected validation, and preserve ordered shared indexes.
14. Run every applicable mandatory closeout stage before marking the specification `completed`.

## Project-Specific Instructions

- Use `uv` for dependency management, locking, testing, building, and installation.
- Keep provider credentials in environment variables or secret injection. Never commit, print, log, return, or place credentials in URLs.
- The supported providers are GitHub and Bitbucket Cloud. The network MCP transport is Streamable HTTP; stdio is retained for local development.
- Bind network services to localhost by default and document authentication/reverse-proxy requirements for remote exposure.
- Keep provider adapters, transport, schemas, authentication, HTTP, normalization, and error mapping separable and testable.

### Feature Closeout Workflow

No project-specific closeout stages are currently declared.

This inert default means no project-specific stage applies. A repository may replace it with explicit release preparation, pull-request, publication, deployment, or other closeout stages when needed. Each declared stage must define a unique human-readable name and execution order; trigger and prerequisite; mandatory or optional status; executor; authority and mutation scope; required inputs and minimum context; separate authorizations; evidence returned to `feature-completion`; passed, failed, unavailable, skipped, and not-applicable semantics; retry and fallback policy; and safe resume condition. A required but unavailable stage must be declared unavailable and blocking rather than omitted.
