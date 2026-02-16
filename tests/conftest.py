from __future__ import annotations

from typing import Any

import pytest
from injector import Injector, Module, provider, singleton

from reaper_mcp.client import ReaperClient
from reaper_mcp.server import create_server


class FakeReaperClient(ReaperClient):
    """In-memory fake that returns canned responses keyed by command type."""

    def __init__(self) -> None:
        self.commands_sent: list[tuple[str, dict[str, Any]]] = []
        self._responses: dict[str, dict[str, Any]] = {}

    def set_response(self, command_type: str, result: dict[str, Any]) -> None:
        self._responses[command_type] = result

    def send_command(
        self, command_type: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        self.commands_sent.append((command_type, params or {}))
        if command_type not in self._responses:
            raise RuntimeError(f"No fake response configured for '{command_type}'")
        return self._responses[command_type]


class FakeReaperModule(Module):
    def __init__(self, fake_client: FakeReaperClient) -> None:
        self._fake_client = fake_client

    @singleton
    @provider
    def provide_reaper_client(self) -> ReaperClient:
        return self._fake_client


@pytest.fixture
def fake_client():
    return FakeReaperClient()


@pytest.fixture
def mcp_server(fake_client):
    injector = Injector([FakeReaperModule(fake_client)])
    return create_server(injector)
