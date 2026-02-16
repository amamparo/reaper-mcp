import json

import pytest


@pytest.mark.anyio
async def test_add_fx(fake_client, mcp_server):
    fake_client.set_response("add_fx", {"fx_index": 0, "name": "ReaEQ"})

    content, _ = await mcp_server.call_tool(
        "add_fx", {"track_index": 0, "fx_name": "ReaEQ"}
    )
    result = json.loads(content[0].text)

    assert result["fx_index"] == 0
    assert result["name"] == "ReaEQ"
    assert fake_client.commands_sent == [
        ("add_fx", {"track_index": 0, "fx_name": "ReaEQ"})
    ]


@pytest.mark.anyio
async def test_remove_fx(fake_client, mcp_server):
    fake_client.set_response("remove_fx", {"removed": True})

    content, _ = await mcp_server.call_tool(
        "remove_fx", {"track_index": 0, "fx_index": 0}
    )
    result = json.loads(content[0].text)

    assert result["removed"] is True
    assert fake_client.commands_sent == [
        ("remove_fx", {"track_index": 0, "fx_index": 0})
    ]


@pytest.mark.anyio
async def test_get_fx_parameters(fake_client, mcp_server):
    fake_client.set_response(
        "get_fx_parameters",
        {
            "fx_name": "ReaEQ",
            "parameters": [
                {
                    "index": 0,
                    "name": "Freq-1",
                    "value": 200.0,
                    "min": 20.0,
                    "max": 20000.0,
                },
                {
                    "index": 1,
                    "name": "Gain-1",
                    "value": 0.0,
                    "min": -24.0,
                    "max": 24.0,
                },
            ],
        },
    )

    content, _ = await mcp_server.call_tool(
        "get_fx_parameters", {"track_index": 0, "fx_index": 0}
    )
    result = json.loads(content[0].text)

    assert result["fx_name"] == "ReaEQ"
    assert len(result["parameters"]) == 2
    assert result["parameters"][0]["name"] == "Freq-1"
    assert fake_client.commands_sent == [
        ("get_fx_parameters", {"track_index": 0, "fx_index": 0})
    ]


@pytest.mark.anyio
async def test_set_fx_parameter(fake_client, mcp_server):
    fake_client.set_response("set_fx_parameter", {"name": "Gain-1", "value": 6.0})

    content, _ = await mcp_server.call_tool(
        "set_fx_parameter",
        {"track_index": 0, "fx_index": 0, "param_index": 1, "value": 6.0},
    )
    result = json.loads(content[0].text)

    assert result["name"] == "Gain-1"
    assert result["value"] == 6.0
    assert fake_client.commands_sent == [
        (
            "set_fx_parameter",
            {
                "track_index": 0,
                "fx_index": 0,
                "param_index": 1,
                "value": 6.0,
            },
        )
    ]


@pytest.mark.anyio
async def test_create_track_with_fx(fake_client, mcp_server):
    fake_client.set_response(
        "create_track_with_fx",
        {
            "track_index": 3,
            "name": "Synth",
            "fx_name": "ReaSynth",
        },
    )

    content, _ = await mcp_server.call_tool(
        "create_track_with_fx",
        {"fx_name": "ReaSynth", "index": -1, "name": "Synth"},
    )
    result = json.loads(content[0].text)

    assert result["track_index"] == 3
    assert result["name"] == "Synth"
    assert result["fx_name"] == "ReaSynth"
    assert fake_client.commands_sent == [
        (
            "create_track_with_fx",
            {"fx_name": "ReaSynth", "index": -1, "name": "Synth"},
        )
    ]
