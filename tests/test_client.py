import pytest

from reaper_mcp.client import ReapyClient

EXPECTED_COMMANDS = {
    "get_project_info",
    "get_track_info",
    "create_track",
    "delete_track",
    "delete_all_tracks",
    "set_track_name",
    "set_track_volume",
    "set_track_pan",
    "set_track_mute",
    "set_track_solo",
    "get_items",
    "create_midi_item",
    "delete_item",
    "duplicate_item",
    "set_item_name",
    "get_item_notes",
    "set_item_notes",
    "start_playback",
    "stop_playback",
    "set_tempo",
    "set_time_signature",
    "undo",
    "set_cursor_position",
    "get_loop_region",
    "set_loop_region",
    "add_fx",
    "remove_fx",
    "get_fx_parameters",
    "set_fx_parameter",
    "create_track_with_fx",
    "add_marker",
    "add_region",
    "get_markers",
}


class TestReapyClient:
    def test_unknown_command_raises_runtime_error(self):
        client = ReapyClient()
        with pytest.raises(RuntimeError, match="Unknown command"):
            client.send_command("nonexistent_command")

    def test_all_commands_registered(self):
        client = ReapyClient()
        assert set(client._commands.keys()) == EXPECTED_COMMANDS

    def test_handler_exception_wrapped_as_runtime_error(self):
        client = ReapyClient()

        def bad_handler():
            raise ValueError("something went wrong")

        client._commands["test_cmd"] = bad_handler
        with pytest.raises(RuntimeError, match="something went wrong"):
            client.send_command("test_cmd")

    def test_runtime_error_not_double_wrapped(self):
        client = ReapyClient()

        def handler_raises_runtime():
            raise RuntimeError("original error")

        client._commands["test_cmd"] = handler_raises_runtime
        with pytest.raises(RuntimeError, match="original error"):
            client.send_command("test_cmd")

    def test_handler_result_returned(self):
        client = ReapyClient()

        def good_handler():
            return {"status": "ok"}

        client._commands["test_cmd"] = good_handler
        result = client.send_command("test_cmd")
        assert result == {"status": "ok"}

    def test_params_passed_as_kwargs(self):
        client = ReapyClient()
        received = {}

        def capturing_handler(**kwargs):
            received.update(kwargs)
            return {"captured": True}

        client._commands["test_cmd"] = capturing_handler
        client.send_command("test_cmd", {"track_index": 0, "name": "Bass"})
        assert received == {"track_index": 0, "name": "Bass"}

    def test_none_params_treated_as_empty(self):
        client = ReapyClient()
        called = [False]

        def no_args_handler():
            called[0] = True
            return {"done": True}

        client._commands["test_cmd"] = no_args_handler
        client.send_command("test_cmd", None)
        assert called[0]
