from unittest.mock import patch

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


class TestAutoConfiguration:
    def test_connection_error_triggers_auto_configure(self):
        client = ReapyClient()

        def handler():
            raise ConnectionRefusedError("Connection refused")

        client._commands["test_cmd"] = handler

        with patch.object(client, "_try_auto_configure", return_value=True):
            with pytest.raises(RuntimeError, match="auto-configured"):
                client.send_command("test_cmd")

    def test_auto_configure_success_message(self):
        client = ReapyClient()

        def handler():
            raise OSError("Connection refused")

        client._commands["test_cmd"] = handler

        with patch.object(client, "_try_auto_configure", return_value=True):
            with pytest.raises(RuntimeError, match="restart REAPER"):
                client.send_command("test_cmd")

    def test_auto_configure_failure_message(self):
        client = ReapyClient()

        def handler():
            raise OSError("Connection refused")

        client._commands["test_cmd"] = handler

        with patch.object(client, "_try_auto_configure", return_value=False):
            with pytest.raises(RuntimeError, match="auto-configuration failed"):
                client.send_command("test_cmd")

    def test_auto_configure_only_attempted_once(self):
        client = ReapyClient()
        call_count = 0

        def handler():
            raise OSError("Connection refused")

        def counting_configure():
            nonlocal call_count
            call_count += 1
            client._auto_configured = True
            return True

        client._commands["test_cmd"] = handler

        with patch.object(
            client, "_try_auto_configure", side_effect=counting_configure
        ):
            with pytest.raises(RuntimeError):
                client.send_command("test_cmd")
            # Second call should not trigger auto-configure
            with pytest.raises(RuntimeError, match="Connection refused"):
                client.send_command("test_cmd")

        assert call_count == 1

    def test_non_connection_error_skips_auto_configure(self):
        client = ReapyClient()

        def handler():
            raise ValueError("bad argument")

        client._commands["test_cmd"] = handler

        with patch.object(client, "_try_auto_configure") as mock_configure:
            with pytest.raises(RuntimeError, match="bad argument"):
                client.send_command("test_cmd")
            mock_configure.assert_not_called()

    def test_is_connection_error_detects_oserror(self):
        assert ReapyClient._is_connection_error(OSError("fail"))
        assert ReapyClient._is_connection_error(ConnectionRefusedError("fail"))

    def test_is_connection_error_detects_reapy_errors(self):
        # Simulate reapy exception classes without importing reapy
        exc = type("DisabledDistAPIError", (Exception,), {})("no api")
        assert ReapyClient._is_connection_error(exc)

        exc = type("DisconnectedClientError", (Exception,), {})("disconnected")
        assert ReapyClient._is_connection_error(exc)

    def test_is_connection_error_rejects_other_exceptions(self):
        assert not ReapyClient._is_connection_error(ValueError("bad"))
        assert not ReapyClient._is_connection_error(TypeError("wrong"))
