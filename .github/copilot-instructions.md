<!-- .github/copilot-instructions.md -->

# Copilot instructions — MSSE-Capstone-Project

Purpose

- Help AI coding agents be productive working on this MCP starter project (Garmin + Weather integration).

- You are an expert in Python, and the MCP Python SDK. Tailor suggestions and code to those expectations.

Quick big-picture

- This repo is a minimal Model Context Protocol (MCP) server starter. The README and architecture image describe the intended design: ingest Garmin activity data, enrich with weather/forecast, and expose an MCP-compatible context provider for agents to query user activity + environment.
- Current implementation is a scaffold: `server.py` contains a tiny `main()` that prints a greeting. Most domain code (Garmin wrapper, weather integration, MCP endpoint handlers) is not yet implemented and should be added under a package (e.g., `msse_capstone/` or `app/`).

Key files and what they mean

- `README.md` — project intent and many TODO sections (design contract, env, auth) that should be filled in as features are added. Update this when adding new endpoints or config requirements.
- `server.py` — current entrypoint; use this as the simplest run target while scaffolding. New services should expand into proper packages and replace or import this module.
- `pyproject.toml` — declares project metadata and dependency `mcp[cli]`. Note Python requirement: `>=3.13`.
- `img/High.Level.Architecture.png` — high-level diagram referenced from README; inspect when implementing cross-component flows.

Integration points (discoverable)

- Garmin: README mentions a Python wrapper for Garmin (not present yet). Expect to add a small client module (for example, `clients/garmin.py`) that handles auth and paging.
- Weather API: external weather/forecast provider to enrich activities (add `clients/weather.py`).
- MCP: `mcp[cli]` dependency indicates the project will expose MCP endpoints and possibly use the MCP CLI for testing and registration. Look for `mcp`-related code as features are added.

How to run and test locally (exact commands)

1. Create a virtualenv and activate it (macOS / zsh):
   - python3.13 -m venv .venv
   - source .venv/bin/activate
2. Install dependencies (two options):
   - Preferred (editable local install — may require adding a [build-system] section to `pyproject.toml`):
     - pip install -e .
   - If packaging install fails, install the MCP CLI directly:
     - pip install "mcp[cli]"
3. Run the current entrypoint:
   - python server.py
4. After adding MCP endpoints, use the MCP CLI (installed by dependency) to inspect or run MCP commands:
   - mcp --help

What not to invent

- The repo currently lacks implementation of Garmin/weather/MCP endpoints. Do not assume hidden modules — add them explicitly and update README and pyproject accordingly.

Where to look next when implementing features

- `README.md` for project intent and architecture diagram in `img/` for cross-component flow.
- `pyproject.toml` to add dependencies.
- Create `tests/` and update README with run instructions when adding logic.

If something is unclear

- Leave TODOs or short comments in `README.md` and the new modules explaining the remaining design choices (auth flow, rate limits, expected request/response shapes). Ask the repo owner for missing external API credentials and expected sample data shapes.

Key principles

- Use functions (def) and type hints for all function signatures where possible.
- Prefer iteration and modularization. Avoid duplicated code.
- Use descriptive variable names with auxiliary verbs: is_active, has_permission, should_retry.
- Filenames and directories: lowercase_with_underscores (e.g., `blueprints/user_routes.py`).
- Favor named exports for routes and utilities (explicit names in **all** or module-level functions).
- Use RORO (Receive an Object, Return an Object) for utility functions and handlers where applicable.

Style notes (Python idioms)

- Python does not use curly braces for blocks. Avoid suggesting brace-like syntax or JS-style constructs.
- Prefer concise one-line conditionals for simple statements when readable (e.g., `if condition: do_something()`).
- Use `def` for function definitions and include type hints for signatures.
- Favor readable, PEP8-compliant formatting; keep lines around 88-100 chars.

Authoritative MCP resources

When designing or implementing MCP-related features, use the following authoritative resources as canonical guidance and reference implementations:

- Model Context Protocol website: https://modelcontextprotocol.io/ — read the protocol overview, concepts, and the spec to align endpoint shapes and behavior.
- Official Python SDK (reference implementation): https://github.com/modelcontextprotocol/python-sdk — consult this repo for client/server examples, data shapes, and helper utilities.

How to use these resources

- Prefer the protocol's type and endpoint shapes from the spec when designing MCP endpoints in this project.
- Use the Python SDK repository for concrete examples (serialization, registration, and testing helpers). When in doubt about expected message shapes or lifecycle, mirror the SDK's approach.
- Cite exact pages or module names from these resources in PR descriptions when implementing MCP functionality so reviewers can validate protocol conformance.
