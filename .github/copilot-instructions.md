<!-- .github/copilot-instructions.md -->

# Copilot instructions — MSSE-Capstone-Project

Purpose

- Help AI coding agents be productive working on this MCP starter project (Garmin + Weather integration).

- You are an expert in Python, Flask, and scalable API development. Tailor suggestions and code to those expectations.

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

Repository conventions and tips for agents

- Small, incremental changes: this is a starter scaffold. Prefer adding new modules under a new package rather than inflating `server.py`.
- Update `README.md` as features land: fill the TODOs for contract, environment variables, and auth flows so future agents (and humans) have a clear contract.
- Keep public APIs stable: if you add package-level entrypoints (for example, `app:create_app()`), document them in README and update the pyproject if new dependencies are required.

Patterns to follow (examples)

- Entrypoint: keep a `main()` and `if __name__ == '__main__'` guard in `server.py` while scaffolding. When adding a web framework, create `app/` with `create_app()` and call it from `server.py`.
- Clients: create `clients/garmin.py` and `clients/weather.py` with a simple sync interface first (fetch(), get_token()). Add async versions later if needed.
- Configuration: prefer environment variables for secrets and API keys. Document required keys in `README.md` as you add them.

What not to invent

- The repo currently lacks implementation of Garmin/weather/MCP endpoints. Do not assume hidden modules — add them explicitly and update README and pyproject accordingly.

Where to look next when implementing features

- `README.md` for project intent and architecture diagram in `img/` for cross-component flow.
- `pyproject.toml` to add dependencies.
- Create `tests/` and update README with run instructions when adding logic.

If something is unclear

- Leave TODOs or short comments in `README.md` and the new modules explaining the remaining design choices (auth flow, rate limits, expected request/response shapes). Ask the repo owner for missing external API credentials and expected sample data shapes.

Feedback

- I created/updated these instructions to match the current scaffold. Tell me which areas you want more detail (examples of MCP handlers, preferred package layout, or exact auth flows) and I will iterate.

Python & Flask conventions (project-specific rules)

These are the authoritative local conventions to follow when implementing the Flask-based API and Python code in this repo. Keep entries short and actionable — prefer examples over prose.

- Expertise expected: Python, Flask, scalable API development.
- Response style: concise, technical, with accurate Python examples. Prefer functional/declarative code; avoid classes except for Flask views when using Flask-RESTful class-based views.

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

Python / Flask specifics

- Use Flask application factory pattern (create_app(config_name: str) -> Flask) for initialization and testing. Place factory in `app/__init__.py` or `msse_capstone/__init__.py`.
- Organize code: `app/` or `msse_capstone/` with subfolders: `blueprints/`, `models/`, `utils/`, `config/`, `clients/`.
- Blueprints: register in the factory. Example pattern: `blueprints/activity_routes.py` -> expose `activity_bp`.
- Use Flask-RESTful for REST APIs and class-based views where it improves clarity; otherwise prefer function-based view functions.
- Use Marshmallow schemas for input validation and serialization; keep schema classes next to models (e.g., `models/activity.py` and `models/activity_schema.py`).

Database interaction

- Use Flask-SQLAlchemy for ORM operations. Keep models in `models/` and migration scripts managed by Flask-Migrate.
- Use SQLAlchemy session scoping and ensure sessions are closed in teardown handlers (or use session scopes/contexts).
- Prefer eager loading and proper indexing for expensive queries; document heavy queries and their expected size.

Serialization and validation

- Use Marshmallow for serialization/deserialization and input validation. Create a schema per model and validate inbound JSON at the edges (controllers/blueprints).

Authentication and authorization

- Use Flask-JWT-Extended for JWT authentication. Provide decorators for protecting routes (e.g., `@jwt_required()`), export reusable auth helpers from `utils/auth.py`.

Testing

- Write unit tests with pytest. Use Flask's test client for functional/integration tests and provide fixtures in `tests/conftest.py` for app and DB setup/teardown.

API documentation

- Use Flask-RESTX or Flasgger to auto-generate Swagger/OpenAPI docs. Ensure endpoints include request/response schemas (Marshmallow) for accurate docs.

Error handling & validation

- Handle errors and edge cases at the top of functions (guard clauses). Use early returns rather than nested if/else.
- Implement custom error types or factories for consistent error responses. Add centralized error handlers in the factory using `app.register_error_handler`.
- Log errors with `app.logger` and return user-friendly error messages with proper HTTP status codes.

Dependencies (recommended)

- Flask
- Flask-RESTful
- Flask-SQLAlchemy
- Flask-Migrate
- Marshmallow
- Flask-JWT-Extended

Flask-specific guidance

- Use before_request/after_request/teardown_request for request lifecycle hooks when needed; keep them small and testable.
- Protect routes with decorators for authentication/authorization (Flask-JWT-Extended). Export reusable decorators from `utils/auth.py`.
- Use Flask-SQLAlchemy for DB access; prefer session scoping and ensure sessions are removed/closed in teardown handlers.

Performance and background work

- Use Flask-Caching for hot data. Prefer read-through caches in util functions.
- Move long-running or blocking tasks to background workers (Celery) and return job ids to clients.

Testing & docs

- Tests: use pytest and Flask's test client. Provide fixtures for the app and database in `tests/conftest.py`.
- Document endpoints with Flask-RESTX or Flasgger; include request/response schema references to Marshmallow schemas.

Deployment

- Use Gunicorn (or uWSGI) as the WSGI server in production. Configure logging and monitoring via environment variables.

Quick examples

- Application factory (minimal):

```python
from flask import Flask

def create_app(config_name: str) -> Flask:
   app = Flask(__name__)
   # ... load config, register blueprints, extensions
   return app
```

- Guard clause pattern (preferred):

```python
def fetch_activity(activity_id: str) -> dict:
   if not activity_id:
      return {"error": "missing activity_id"}, 400
   # happy path last
   activity = _load_from_db(activity_id)
   return activity
```

Authoritative MCP resources

When designing or implementing MCP-related features, use the following authoritative resources as canonical guidance and reference implementations:

- Model Context Protocol website: https://modelcontextprotocol.io/ — read the protocol overview, concepts, and the spec to align endpoint shapes and behavior.
- Official Python SDK (reference implementation): https://github.com/modelcontextprotocol/python-sdk — consult this repo for client/server examples, data shapes, and helper utilities.

How to use these resources

- Prefer the protocol's type and endpoint shapes from the spec when designing MCP endpoints in this project.
- Use the Python SDK repository for concrete examples (serialization, registration, and testing helpers). When in doubt about expected message shapes or lifecycle, mirror the SDK's approach.
- Cite exact pages or module names from these resources in PR descriptions when implementing MCP functionality so reviewers can validate protocol conformance.
