import json

import pytest


@pytest.mark.anyio
async def test_add_marker(fake_client, mcp_server):
    fake_client.set_response(
        "add_marker", {"marker_index": 0, "position": 16.0, "name": "Chorus"}
    )

    content, _ = await mcp_server.call_tool(
        "add_marker", {"position": 16.0, "name": "Chorus"}
    )
    result = json.loads(content[0].text)

    assert result["marker_index"] == 0
    assert result["position"] == 16.0
    assert result["name"] == "Chorus"
    assert fake_client.commands_sent == [
        ("add_marker", {"position": 16.0, "name": "Chorus"})
    ]


@pytest.mark.anyio
async def test_add_region(fake_client, mcp_server):
    fake_client.set_response(
        "add_region",
        {"region_index": 0, "start": 0.0, "end": 32.0, "name": "Intro"},
    )

    content, _ = await mcp_server.call_tool(
        "add_region", {"start": 0.0, "end": 32.0, "name": "Intro"}
    )
    result = json.loads(content[0].text)

    assert result["region_index"] == 0
    assert result["start"] == 0.0
    assert result["end"] == 32.0
    assert result["name"] == "Intro"


@pytest.mark.anyio
async def test_get_markers(fake_client, mcp_server):
    fake_client.set_response(
        "get_markers",
        {
            "markers": [{"index": 0, "name": "Chorus", "position": 16.0}],
            "regions": [{"index": 0, "name": "Intro", "start": 0.0, "end": 32.0}],
        },
    )

    content, _ = await mcp_server.call_tool("get_markers", {})
    result = json.loads(content[0].text)

    assert len(result["markers"]) == 1
    assert len(result["regions"]) == 1
    assert result["markers"][0]["name"] == "Chorus"
    assert result["regions"][0]["name"] == "Intro"
    assert fake_client.commands_sent == [("get_markers", {})]
