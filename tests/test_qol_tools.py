import json

import pytest


@pytest.mark.anyio
async def test_set_time_signature(fake_client, mcp_server):
    fake_client.set_response(
        "set_time_signature",
        {"signature_numerator": 5, "signature_denominator": 4},
    )

    content, _ = await mcp_server.call_tool(
        "set_time_signature", {"numerator": 5, "denominator": 4}
    )
    result = json.loads(content[0].text)

    assert result["signature_numerator"] == 5
    assert result["signature_denominator"] == 4
    assert fake_client.commands_sent == [
        ("set_time_signature", {"numerator": 5, "denominator": 4})
    ]


@pytest.mark.anyio
async def test_undo(fake_client, mcp_server):
    fake_client.set_response("undo", {"undone": True})

    content, _ = await mcp_server.call_tool("undo", {})
    result = json.loads(content[0].text)

    assert result["undone"] is True
    assert fake_client.commands_sent == [("undo", {})]
