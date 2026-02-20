# AI Coding Agent Instructions

Last updated: 2026-01-24

This repository currently has no source files. Until code exists, agents should focus on discovery, scaffolding, and capturing decisions so future work is consistent and immediately productive.

## Discovery First
- Verify workspace contents and branch: run `ls -la` at repo root; confirm you’re on the intended project.
- If files are missing, ask the maintainer to sync or point to the correct workspace.
- When files appear, document build/test commands and conventions in this file and `README.md`.

## Scaffolding Guidance (YouTube System Design)
- Prefer modular folders that mirror major components (suggested):
  - `api-gateway/`, `video-upload/`, `transcoding/`, `storage/`, `cdn/`, `metadata/`, `search/`, `recommendations/`, `analytics/`.
- Add a top-level `README.md` describing:
  - Component boundaries, data flows (upload → encode → store → serve; metadata → index → search), and reasons for key trade-offs (latency, cost, scalability).
  - Operational workflows: local run, tests, and debugging.

## Project Conventions to Capture (once code exists)
- Language/runtime and package manager (e.g., Node.js with `pnpm`, Python with `poetry`).
- Service layout: monorepo vs multi-service directories, common libraries.
- Config strategy: `.env` files, secrets handling, and config overrides per environment.
- Interface contracts: API schemas (OpenAPI), message formats (Kafka/SQS), and storage schemas.
- Testing: levels (unit/integration/e2e), locations, runners, and naming.
- CI/CD: pipelines, lint/format rules, and required checks.

## Developer Workflows (to document concretely)
- Build/run: exact commands for local start of each component.
- Tests: how to run fast unit tests and slower integration tests.
- Debug: common breakpoints, log levels, and tracing.
- Data: local dev data seeding/scripts and safe resets.

## Cross-Component Patterns (examples to add as they appear)
- Async pipelines for upload/transcode/store: queue/topic names, retry and idempotency rules.
- Metadata indexing/search: write/read paths, eventual consistency notes.
- CDN and edge caching: cache keys, invalidation strategies.
- Observability: logs/metrics/traces and standard fields across services.

## How Agents Should Work Here
- Be explicit about assumptions; confirm with maintainers when unclear.
- Keep changes minimal and focused; avoid refactors without strong rationale.
- Update this file and `README.md` when you discover build commands, test setups, or conventions.
- Prefer adding small, runnable examples (scripts or tiny services) to validate patterns before scaling.

## Next Steps
- Add initial `README.md` with architecture overview and a minimal component scaffold.
- Once code is added, replace placeholders above with the real commands, directories, and patterns.

If any section is unclear or incomplete, please share details about your planned architecture, language/runtime, and desired developer workflow so I can tailor this document to the actual codebase.