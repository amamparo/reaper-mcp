# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

All commands run via `just` (see `justfile`):

- `just check` — run lint + tests (default)
- `just lint` — Black formatting check + Ruff linting
- `just test` — run pytest
- `just fmt` — auto-format with Black
- `just install` — install Poetry dependencies
- `poetry run pytest tests/test_file.py::test_name` — run a single test

## Architecture

This is an MCP (Model Context Protocol) server for REAPER, built with FastMCP.

**Single component:** The MCP server (`src/reaper_mcp/`) uses [python-reapy](https://github.com/RomeoDespres/reapy) to control REAPER directly — no custom scripts or TCP bridges needed. reapy communicates with REAPER through its built-in dist API.

**Key files:**
- `src/reaper_mcp/server.py` — MCP server factory and tool definitions
- `src/reaper_mcp/client.py` — `ReaperClient` ABC and `ReapyClient` (reapy-based)
- `src/reaper_mcp/__main__.py` — entrypoint (`reaper-mcp` CLI command)

**Dependency injection:** Uses the `injector` library. `ReaperClient` is bound in `ReaperModule` and resolved via `injector.get()` inside tool handlers. The `create_server()` factory accepts an optional `Injector` to allow swapping implementations in tests.

**Testing pattern:** Tests use `@pytest.mark.anyio` for async. Call tools directly via `mcp.call_tool(name, args)` which returns `(content_list, raw_result)`. Pass a custom `Injector` to `create_server()` with `FakeReaperClient` (see `tests/conftest.py`).

**reapy setup:** One-time: `python -c "import reapy; reapy.configure_reaper()"` then restart REAPER. The `ReapyClient` uses `reapy.reascript_api` (lazily imported) to call REAPER's API functions directly.

## Code Style

- Python 3.12+, PEP 8, Black with 88-char line length
- Ruff for linting (rules: E, F, I, W)
