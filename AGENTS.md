# Repository Guidelines

## Project Structure & Source of Truth

This repository is the implementation target for AgentReliability Hub. Follow the sibling steering pack at `../agent-reliability-steering-pack 2/`: `docs/PRD.md` defines scope, `docs/SRS.md` behavior, `docs/CONTRACTS.md` wire formats, and `docs/ARCHITECTURE.md` boundaries. Record build and learning evidence separately in `learning/PROGRESS.md` when those files are merged into this repository.

Use the planned layout: `app/` for FastAPI setup, schemas, database code, and routes; `app/services/` for runner, evaluator, scoring, and reports; `app/adapters/` for the deterministic mock; `app/static/` for browser assets; and `tests/` for pytest suites. Keep evaluator logic independent of HTTP and storage.

## Build, Test, and Development Commands

Run commands from the repository root. The project is not scaffolded yet, so verify commands as each dependency is added:

- `python3 -m venv .venv` creates the isolated environment.
- `source .venv/bin/activate` activates it on macOS/Linux.
- `python -m pytest` runs the automated suite.
- `python -m uvicorn app.main:app --reload` starts the local server.

Document only commands that have actually been run successfully.

## Coding Style & Architecture

Use four-space indentation, `snake_case` for functions and modules, `PascalCase` for classes, and type hints at service boundaries. Validate external data with Pydantic. Keep routes thin, database sessions bounded, fixtures deterministic, and historical run snapshots immutable. Prefer straightforward functions over unused abstractions.

## Testing Guidelines

Name tests `test_<module>.py` and test functions `test_<behavior>`. Cover golden evaluator cases, threshold boundaries, unknown metrics, case-error continuation, project isolation, rollback, restart persistence, report parity, and CLI exit codes. Use temporary SQLite databases. A check counts as passed only after execution; record the command and observed result.

## Commit & Pull Request Guidelines

History currently contains only `Initial commit`. Use focused, imperative subjects such as `Add scoring boundary tests`. PRs must describe changed behavior, linked requirements or issues, commands run with results, limitations, and screenshots for UI changes.

## Security and Claims

Keep the MVP local and mock-based. Do not commit credentials, `.venv/`, or database files. Label synthetic and unknown metrics accurately. A passing configured gate is evidence for that suite, not production-safety certification.
