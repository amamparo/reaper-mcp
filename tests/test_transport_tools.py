import json

import pytest


@pytest.mark.anyio
async def test_start_playback(fake_client, mcp_server):
    fake_client.set_response("start_playback", {"playing": True})

    content, _ = await mcp_server.call_tool("start_playback", {})
    result = json.loads(content[0].text)

    assert result["playing"] is True
    assert fake_client.commands_sent == [("start_playback", {})]


@pytest.mark.anyio
async def test_stop_playback(fake_client, mcp_server):
    fake_client.set_response("stop_playback", {"playing": False})

    content, _ = await mcp_server.call_tool("stop_playback", {})
    result = json.loads(content[0].text)

    assert result["playing"] is False


@pytest.mark.anyio
async def test_set_tempo(fake_client, mcp_server):
    fake_client.set_response("set_tempo", {"tempo": 140.0})

    content, _ = await mcp_server.call_tool("set_tempo", {"tempo": 140.0})
    result = json.loads(content[0].text)

    assert result["tempo"] == 140.0
    assert fake_client.commands_sent == [("set_tempo", {"tempo": 140.0})]


@pytest.mark.anyio
async def test_set_cursor_position(fake_client, mcp_server):
    fake_client.set_response("set_cursor_position", {"cursor_position": 16.0})

    content, _ = await mcp_server.call_tool("set_cursor_position", {"time": 16.0})
    result = json.loads(content[0].text)

    assert result["cursor_position"] == 16.0
    assert fake_client.commands_sent == [("set_cursor_position", {"time": 16.0})]


@pytest.mark.anyio
async def test_get_loop_region(fake_client, mcp_server):
    fake_client.set_response(
        "get_loop_region", {"loop_start": 0.0, "loop_length": 16.0}
    )

    content, _ = await mcp_server.call_tool("get_loop_region", {})
    result = json.loads(content[0].text)

    assert result["loop_start"] == 0.0
    assert result["loop_length"] == 16.0


@pytest.mark.anyio
async def test_set_loop_region(fake_client, mcp_server):
    fake_client.set_response(
        "set_loop_region", {"loop_start": 8.0, "loop_length": 32.0}
    )

    content, _ = await mcp_server.call_tool(
        "set_loop_region", {"start": 8.0, "length": 32.0}
    )
    result = json.loads(content[0].text)

    assert result["loop_start"] == 8.0
    assert result["loop_length"] == 32.0
