import json

from injector import Injector, Module, provider, singleton
from mcp.server.fastmcp import FastMCP

from reaper_mcp.client import ReaperClient, ReapyClient


class ReaperModule(Module):
    @singleton
    @provider
    def provide_reaper_client(self) -> ReaperClient:
        return ReapyClient()


def create_server(injector: Injector | None = None) -> FastMCP:
    if injector is None:
        injector = Injector([ReaperModule])

    mcp = FastMCP("reaper-mcp")

    def _client() -> ReaperClient:
        return injector.get(ReaperClient)

    def _call(command_type: str, params: dict | None = None) -> str:
        try:
            result = _client().send_command(command_type, params)
            return json.dumps(result, indent=2)
        except RuntimeError as e:
            return json.dumps({"error": str(e)})

    # ── Project / Info ───────────────────────────────────────────────

    @mcp.tool()
    def get_project_info() -> str:
        """Get current REAPER project info: tempo, time signature,
        track count, play state, and cursor position."""
        return _call("get_project_info")

    @mcp.tool()
    def get_track_info(track_index: int) -> str:
        """Get detailed info about a track: name, mute/solo/arm state,
        volume, pan, media items, and FX chain."""
        return _call("get_track_info", {"track_index": track_index})

    # ── Track Management ─────────────────────────────────────────────

    @mcp.tool()
    def create_track(index: int = -1) -> str:
        """Create a new track. Use index=-1 to append at the end.
        REAPER tracks handle both audio and MIDI."""
        return _call("create_track", {"index": index})

    @mcp.tool()
    def delete_track(track_index: int) -> str:
        """Delete a track by index."""
        return _call("delete_track", {"track_index": track_index})

    @mcp.tool()
    def delete_all_tracks() -> str:
        """Delete all tracks. Useful for clearing a project before
        building a fresh arrangement. Returns the count of deleted tracks."""
        return _call("delete_all_tracks")

    @mcp.tool()
    def set_track_name(track_index: int, name: str) -> str:
        """Rename a track."""
        return _call("set_track_name", {"track_index": track_index, "name": name})

    @mcp.tool()
    def set_track_volume(track_index: int, volume: float) -> str:
        """Set track volume. Range: 0.0 (silence) to 1.0 (unity gain)."""
        return _call("set_track_volume", {"track_index": track_index, "volume": volume})

    @mcp.tool()
    def set_track_pan(track_index: int, pan: float) -> str:
        """Set track pan. Range: -1.0 (full left) to 1.0 (full right),
        0.0 is center."""
        return _call("set_track_pan", {"track_index": track_index, "pan": pan})

    @mcp.tool()
    def set_track_mute(track_index: int, mute: bool) -> str:
        """Mute or unmute a track."""
        return _call("set_track_mute", {"track_index": track_index, "mute": mute})

    @mcp.tool()
    def set_track_solo(track_index: int, solo: bool) -> str:
        """Solo or unsolo a track."""
        return _call("set_track_solo", {"track_index": track_index, "solo": solo})

    # ── Media Items ──────────────────────────────────────────────────

    @mcp.tool()
    def get_items(track_index: int) -> str:
        """Get all media items on a track. Returns each item's index, name,
        position, length, and whether it contains MIDI."""
        return _call("get_items", {"track_index": track_index})

    @mcp.tool()
    def create_midi_item(track_index: int, position: float, length: float = 4.0) -> str:
        """Create an empty MIDI item on a track. Position and length are
        in beats."""
        return _call(
            "create_midi_item",
            {
                "track_index": track_index,
                "position": position,
                "length": length,
            },
        )

    @mcp.tool()
    def delete_item(track_index: int, item_index: int) -> str:
        """Delete a media item from a track by index.
        Use get_items to find the item_index."""
        return _call(
            "delete_item",
            {"track_index": track_index, "item_index": item_index},
        )

    @mcp.tool()
    def duplicate_item(
        track_index: int, item_index: int, destination_time: float
    ) -> str:
        """Duplicate a media item to a new position on the same track.
        destination_time is in beats."""
        return _call(
            "duplicate_item",
            {
                "track_index": track_index,
                "item_index": item_index,
                "destination_time": destination_time,
            },
        )

    @mcp.tool()
    def set_item_name(track_index: int, item_index: int, name: str) -> str:
        """Rename a media item's active take."""
        return _call(
            "set_item_name",
            {
                "track_index": track_index,
                "item_index": item_index,
                "name": name,
            },
        )

    # ── MIDI Notes ───────────────────────────────────────────────────

    @mcp.tool()
    def get_item_notes(track_index: int, item_index: int) -> str:
        """Read all MIDI notes from a media item's active take.
        Returns a list of notes with pitch, start_time (beats),
        duration (beats), velocity, and mute."""
        return _call(
            "get_item_notes",
            {"track_index": track_index, "item_index": item_index},
        )

    @mcp.tool()
    def set_item_notes(
        track_index: int,
        item_index: int,
        notes: list[dict],
        append: bool = False,
    ) -> str:
        """Set MIDI notes on a media item's active take. Each note is a dict
        with keys: pitch (0-127), start_time (beats), duration (beats),
        velocity (0-127, default 100), mute (bool, default false).
        By default this replaces all existing notes.
        Set append=true to keep existing notes and add new ones."""
        return _call(
            "set_item_notes",
            {
                "track_index": track_index,
                "item_index": item_index,
                "notes": notes,
                "append": append,
            },
        )

    # ── Transport ────────────────────────────────────────────────────

    @mcp.tool()
    def start_playback() -> str:
        """Start project playback."""
        return _call("start_playback")

    @mcp.tool()
    def stop_playback() -> str:
        """Stop project playback."""
        return _call("stop_playback")

    @mcp.tool()
    def set_tempo(tempo: float) -> str:
        """Set the project tempo in BPM."""
        return _call("set_tempo", {"tempo": tempo})

    @mcp.tool()
    def set_time_signature(numerator: int, denominator: int) -> str:
        """Set the project time signature (e.g. 4/4, 5/4, 7/8)."""
        return _call(
            "set_time_signature",
            {"numerator": numerator, "denominator": denominator},
        )

    @mcp.tool()
    def undo() -> str:
        """Trigger REAPER's undo. Safety net for destructive operations."""
        return _call("undo")

    @mcp.tool()
    def set_cursor_position(time: float) -> str:
        """Set the edit cursor position in beats."""
        return _call("set_cursor_position", {"time": time})

    @mcp.tool()
    def get_loop_region() -> str:
        """Get the loop/repeat region position and length in beats."""
        return _call("get_loop_region")

    @mcp.tool()
    def set_loop_region(start: float, length: float) -> str:
        """Set the loop/repeat region. start and length are in beats."""
        return _call("set_loop_region", {"start": start, "length": length})

    # ── FX ───────────────────────────────────────────────────────────

    @mcp.tool()
    def add_fx(track_index: int, fx_name: str) -> str:
        """Add an FX plugin to a track by name. The name is searched against
        installed VST/AU/JS plugins. Returns the FX index and resolved name."""
        return _call("add_fx", {"track_index": track_index, "fx_name": fx_name})

    @mcp.tool()
    def remove_fx(track_index: int, fx_index: int) -> str:
        """Remove an FX from a track's FX chain by index."""
        return _call("remove_fx", {"track_index": track_index, "fx_index": fx_index})

    @mcp.tool()
    def get_fx_parameters(track_index: int, fx_index: int) -> str:
        """List all parameters of an FX on a track.
        Returns fx_name and a list of parameters with name, value, min, max."""
        return _call(
            "get_fx_parameters",
            {"track_index": track_index, "fx_index": fx_index},
        )

    @mcp.tool()
    def set_fx_parameter(
        track_index: int, fx_index: int, param_index: int, value: float
    ) -> str:
        """Set an FX parameter value. Value is clamped to the parameter's
        min/max range. Use get_fx_parameters to discover available parameters."""
        return _call(
            "set_fx_parameter",
            {
                "track_index": track_index,
                "fx_index": fx_index,
                "param_index": param_index,
                "value": value,
            },
        )

    @mcp.tool()
    def create_track_with_fx(fx_name: str, index: int = -1, name: str = "") -> str:
        """Create a new track and add an FX plugin in a single operation.
        Faster than separate create_track + add_fx calls.
        Use index=-1 to append at the end. Optionally set the track name."""
        params: dict = {"fx_name": fx_name, "index": index}
        if name:
            params["name"] = name
        return _call("create_track_with_fx", params)

    # ── Markers / Regions ────────────────────────────────────────────

    @mcp.tool()
    def add_marker(position: float, name: str = "") -> str:
        """Add a project marker at a position in beats."""
        return _call("add_marker", {"position": position, "name": name})

    @mcp.tool()
    def add_region(start: float, end: float, name: str = "") -> str:
        """Add a project region spanning from start to end (in beats)."""
        return _call("add_region", {"start": start, "end": end, "name": name})

    @mcp.tool()
    def get_markers() -> str:
        """List all project markers and regions with their positions in beats."""
        return _call("get_markers")

    return mcp


mcp = create_server()
