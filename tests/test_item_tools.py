import json

import pytest


@pytest.mark.anyio
async def test_get_items(fake_client, mcp_server):
    fake_client.set_response(
        "get_items",
        {
            "items": [
                {
                    "index": 0,
                    "name": "Intro",
                    "position": 0.0,
                    "length": 16.0,
                    "is_midi": True,
                },
                {
                    "index": 1,
                    "name": "Verse",
                    "position": 16.0,
                    "length": 32.0,
                    "is_midi": True,
                },
            ]
        },
    )

    content, _ = await mcp_server.call_tool("get_items", {"track_index": 0})
    result = json.loads(content[0].text)

    assert len(result["items"]) == 2
    assert result["items"][0]["name"] == "Intro"
    assert result["items"][1]["position"] == 16.0
    assert fake_client.commands_sent == [("get_items", {"track_index": 0})]


@pytest.mark.anyio
async def test_create_midi_item(fake_client, mcp_server):
    fake_client.set_response(
        "create_midi_item",
        {"track_index": 0, "position": 8.0, "length": 4.0},
    )

    content, _ = await mcp_server.call_tool(
        "create_midi_item",
        {"track_index": 0, "position": 8.0, "length": 4.0},
    )
    result = json.loads(content[0].text)

    assert result["position"] == 8.0
    assert result["length"] == 4.0
    assert fake_client.commands_sent == [
        (
            "create_midi_item",
            {"track_index": 0, "position": 8.0, "length": 4.0},
        )
    ]


@pytest.mark.anyio
async def test_create_midi_item_default_length(fake_client, mcp_server):
    fake_client.set_response(
        "create_midi_item",
        {"track_index": 0, "position": 0.0, "length": 4.0},
    )

    await mcp_server.call_tool("create_midi_item", {"track_index": 0, "position": 0.0})

    assert fake_client.commands_sent == [
        ("create_midi_item", {"track_index": 0, "position": 0.0, "length": 4.0})
    ]


@pytest.mark.anyio
async def test_delete_item(fake_client, mcp_server):
    fake_client.set_response("delete_item", {"deleted": True})

    content, _ = await mcp_server.call_tool(
        "delete_item", {"track_index": 0, "item_index": 1}
    )
    result = json.loads(content[0].text)

    assert result["deleted"] is True


@pytest.mark.anyio
async def test_duplicate_item(fake_client, mcp_server):
    fake_client.set_response(
        "duplicate_item",
        {"duplicated": True, "destination_time": 32.0},
    )

    content, _ = await mcp_server.call_tool(
        "duplicate_item",
        {"track_index": 0, "item_index": 0, "destination_time": 32.0},
    )
    result = json.loads(content[0].text)

    assert result["duplicated"] is True
    assert result["destination_time"] == 32.0


@pytest.mark.anyio
async def test_set_item_name(fake_client, mcp_server):
    fake_client.set_response("set_item_name", {"name": "Chorus"})

    content, _ = await mcp_server.call_tool(
        "set_item_name",
        {"track_index": 0, "item_index": 0, "name": "Chorus"},
    )
    result = json.loads(content[0].text)

    assert result["name"] == "Chorus"


@pytest.mark.anyio
async def test_get_item_notes(fake_client, mcp_server):
    fake_client.set_response(
        "get_item_notes",
        {
            "notes": [
                {
                    "pitch": 60,
                    "start_time": 0.0,
                    "duration": 1.0,
                    "velocity": 100,
                    "mute": False,
                },
                {
                    "pitch": 64,
                    "start_time": 1.0,
                    "duration": 0.5,
                    "velocity": 80,
                    "mute": False,
                },
            ]
        },
    )

    content, _ = await mcp_server.call_tool(
        "get_item_notes", {"track_index": 0, "item_index": 0}
    )
    result = json.loads(content[0].text)

    assert len(result["notes"]) == 2
    assert result["notes"][0]["pitch"] == 60
    assert result["notes"][1]["velocity"] == 80
    assert fake_client.commands_sent == [
        ("get_item_notes", {"track_index": 0, "item_index": 0})
    ]


@pytest.mark.anyio
async def test_set_item_notes(fake_client, mcp_server):
    notes = [
        {"pitch": 60, "start_time": 0.0, "duration": 0.5, "velocity": 100},
        {"pitch": 67, "start_time": 0.5, "duration": 0.5, "velocity": 80},
    ]
    fake_client.set_response("set_item_notes", {"notes_set": 2})

    content, _ = await mcp_server.call_tool(
        "set_item_notes",
        {"track_index": 0, "item_index": 0, "notes": notes},
    )
    result = json.loads(content[0].text)

    assert result["notes_set"] == 2


@pytest.mark.anyio
async def test_set_item_notes_append(fake_client, mcp_server):
    notes = [{"pitch": 67, "start_time": 2.0, "duration": 1.0, "velocity": 90}]
    fake_client.set_response("set_item_notes", {"notes_set": 1})

    content, _ = await mcp_server.call_tool(
        "set_item_notes",
        {"track_index": 0, "item_index": 0, "notes": notes, "append": True},
    )
    result = json.loads(content[0].text)

    assert result["notes_set"] == 1
    assert fake_client.commands_sent[0] == (
        "set_item_notes",
        {"track_index": 0, "item_index": 0, "notes": notes, "append": True},
    )
