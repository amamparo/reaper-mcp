# reaper-mcp

MCP server for controlling REAPER — enabling AI assistants to interact with REAPER projects via the Model Context Protocol.

## Prerequisites

- **REAPER 7+** with Python 3 ReaScript support enabled
- **Python 3.12+**

## Setup

### 1. Enable reapy

The MCP server uses [python-reapy](https://github.com/RomeoDespres/reapy) to communicate with REAPER. On the first connection attempt, the server will automatically run `reapy.configure_reaper()` if needed. After that, **restart REAPER once** for the changes to take effect.

If auto-configuration fails (e.g. REAPER's resource path can't be found), you can run it manually:

```bash
pip install python-reapy
python -c "import reapy; reapy.configure_reaper()"
```

Then restart REAPER.

### 2. Configure Your MCP Client

Add the server to your MCP client's configuration. The server name is `reaper-mcp` and it runs via `uvx`.

**Generic MCP client config (JSON):**

```json
{
  "mcpServers": {
    "reaper-mcp": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/amamparo/reaper-mcp", "reaper-mcp"]
    }
  }
}
```

To pin to a specific version:

```json
{
  "mcpServers": {
    "reaper-mcp": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/amamparo/reaper-mcp@v0.1.0", "reaper-mcp"]
    }
  }
}
```

**CLI-based clients** (e.g. Claude Code):

```bash
claude mcp add reaper-mcp -- uvx --from "git+https://github.com/amamparo/reaper-mcp" reaper-mcp
```

## Available Tools

| Tool | Description |
|------|-------------|
| `get_project_info` | Get tempo, time signature, track count, play state |
| `get_track_info` | Get track details (name, volume, pan, items, FX) |
| `create_track` | Create a new track |
| `delete_track` | Delete a track |
| `delete_all_tracks` | Delete all tracks (clear project) |
| `set_track_name` | Rename a track |
| `set_track_volume` | Set track volume (0.0–1.0) |
| `set_track_pan` | Set track pan (-1.0–1.0) |
| `set_track_mute` | Mute/unmute a track |
| `set_track_solo` | Solo/unsolo a track |
| `get_items` | List media items on a track |
| `create_midi_item` | Create an empty MIDI item |
| `delete_item` | Delete a media item |
| `duplicate_item` | Duplicate a media item to a new position |
| `set_item_name` | Rename a media item |
| `get_item_notes` | Read MIDI notes from an item |
| `set_item_notes` | Set MIDI notes on an item |
| `start_playback` | Start project playback |
| `stop_playback` | Stop project playback |
| `set_tempo` | Set tempo in BPM |
| `set_time_signature` | Set time signature (e.g. 5/4, 7/8) |
| `undo` | Trigger REAPER's undo |
| `set_cursor_position` | Set the edit cursor position |
| `get_loop_region` | Get the loop/repeat region |
| `set_loop_region` | Set the loop/repeat region |
| `add_fx` | Add an FX plugin to a track |
| `remove_fx` | Remove an FX from a track |
| `get_fx_parameters` | List all parameters of an FX |
| `set_fx_parameter` | Set an FX parameter value |
| `create_track_with_fx` | Create a track and add FX in one step |
| `add_marker` | Add a project marker |
| `add_region` | Add a project region |
| `get_markers` | List all markers and regions |

## Development

```bash
just install           # Install dependencies
just check             # Run lint + tests
just fmt               # Auto-format code
```
