from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ReaperClient(ABC):
    """Abstract interface for communicating with REAPER."""

    @abstractmethod
    def send_command(
        self, command_type: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Send a command and return the result dict.

        Raises RuntimeError on connection or protocol errors.
        """
        ...


class ReapyClient(ReaperClient):
    """Controls REAPER directly via the reapy library.

    On first connection failure, automatically runs
    ``reapy.configure_reaper()`` and asks the user to restart REAPER.
    """

    def __init__(self) -> None:
        self._api_module: Any = None
        self._auto_configured = False
        self._commands: dict[str, Any] = {
            "get_project_info": self._get_project_info,
            "get_track_info": self._get_track_info,
            "create_track": self._create_track,
            "delete_track": self._delete_track,
            "delete_all_tracks": self._delete_all_tracks,
            "set_track_name": self._set_track_name,
            "set_track_volume": self._set_track_volume,
            "set_track_pan": self._set_track_pan,
            "set_track_mute": self._set_track_mute,
            "set_track_solo": self._set_track_solo,
            "get_items": self._get_items,
            "create_midi_item": self._create_midi_item,
            "delete_item": self._delete_item,
            "duplicate_item": self._duplicate_item,
            "set_item_name": self._set_item_name,
            "get_item_notes": self._get_item_notes,
            "set_item_notes": self._set_item_notes,
            "start_playback": self._start_playback,
            "stop_playback": self._stop_playback,
            "set_tempo": self._set_tempo,
            "set_time_signature": self._set_time_signature,
            "undo": self._undo,
            "set_cursor_position": self._set_cursor_position,
            "get_loop_region": self._get_loop_region,
            "set_loop_region": self._set_loop_region,
            "add_fx": self._add_fx,
            "remove_fx": self._remove_fx,
            "get_fx_parameters": self._get_fx_parameters,
            "set_fx_parameter": self._set_fx_parameter,
            "create_track_with_fx": self._create_track_with_fx,
            "add_marker": self._add_marker,
            "add_region": self._add_region,
            "get_markers": self._get_markers,
        }

    @property
    def _api(self) -> Any:
        """Lazily import reapy.reascript_api on first use."""
        if self._api_module is None:
            import reapy  # noqa: F401
            import reapy.reascript_api

            self._api_module = reapy.reascript_api
        return self._api_module

    def send_command(
        self, command_type: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        handler = self._commands.get(command_type)
        if handler is None:
            raise RuntimeError(f"Unknown command: {command_type}")
        try:
            return handler(**(params or {}))
        except RuntimeError:
            raise
        except Exception as e:
            if not self._auto_configured and self._is_connection_error(e):
                configured = self._try_auto_configure()
                if configured:
                    raise RuntimeError(
                        "Could not connect to REAPER. reapy has been "
                        "auto-configured — please restart REAPER and "
                        "try again."
                    ) from e
                raise RuntimeError(
                    "Could not connect to REAPER and auto-configuration "
                    'failed. Please run: python -c "import reapy; '
                    'reapy.configure_reaper()" then restart REAPER.'
                ) from e
            raise RuntimeError(str(e)) from e

    @staticmethod
    def _is_connection_error(exc: Exception) -> bool:
        if isinstance(exc, OSError):
            return True
        name = type(exc).__name__
        return name in ("DisabledDistAPIError", "DisconnectedClientError")

    def _try_auto_configure(self) -> bool:
        """Attempt reapy.configure_reaper(). Returns True on success."""
        self._auto_configured = True
        self._api_module = None
        try:
            import reapy

            reapy.configure_reaper()
            return True
        except Exception:
            return False

    # ── Helpers ───────────────────────────────────────────────────────

    def _get_track(self, track_index: int) -> Any:
        count = self._api.CountTracks(0)
        if track_index < 0 or track_index >= count:
            raise ValueError(f"Track index {track_index} out of range (0-{count - 1})")
        return self._api.GetTrack(0, track_index)

    def _get_item(self, track_index: int, item_index: int) -> Any:
        track = self._get_track(track_index)
        count = self._api.CountTrackMediaItems(track)
        if item_index < 0 or item_index >= count:
            raise ValueError(f"Item index {item_index} out of range (0-{count - 1})")
        return self._api.GetTrackMediaItem(track, item_index)

    def _get_active_take(self, track_index: int, item_index: int) -> Any:
        item = self._get_item(track_index, item_index)
        take = self._api.GetActiveTake(item)
        if not take:
            raise ValueError(
                f"No active take on item {item_index}, track {track_index}"
            )
        return take

    def _beats_to_time(self, beats: float) -> float:
        return self._api.TimeMap2_QNToTime(0, float(beats))

    def _time_to_beats(self, time_sec: float) -> float:
        return self._api.TimeMap2_timeToQN(0, float(time_sec))

    def _ppq_to_beats(self, take: Any, ppq: float) -> float:
        proj_time = self._api.MIDI_GetProjTimeFromPPQPos(take, ppq)
        return self._time_to_beats(proj_time)

    def _beats_to_ppq(self, take: Any, beats: float) -> float:
        proj_time = self._beats_to_time(beats)
        return self._api.MIDI_GetPPQPosFromProjTime(take, proj_time)

    # ── Project / Info ────────────────────────────────────────────────

    def _get_project_info(self) -> dict[str, Any]:
        RPR = self._api
        tempo, bpi = RPR.GetProjectTimeSignature2(0, 0, 0)[1:]
        play_state = RPR.GetPlayState()
        cursor = self._time_to_beats(RPR.GetCursorPosition())
        return {
            "tempo": tempo,
            "signature_numerator": int(bpi),
            "signature_denominator": 4,
            "track_count": RPR.CountTracks(0),
            "is_playing": bool(play_state & 1),
            "is_recording": bool(play_state & 4),
            "cursor_position": cursor,
        }

    def _get_track_info(self, track_index: int) -> dict[str, Any]:
        RPR = self._api
        track = self._get_track(track_index)

        _, _, _, name, _ = RPR.GetSetMediaTrackInfo_String(track, "P_NAME", "", False)

        items = []
        for i in range(RPR.CountTrackMediaItems(track)):
            item = RPR.GetTrackMediaItem(track, i)
            pos = RPR.GetMediaItemInfo_Value(item, "D_POSITION")
            length = RPR.GetMediaItemInfo_Value(item, "D_LENGTH")
            take = RPR.GetActiveTake(item)
            take_name = ""
            is_midi = False
            if take:
                _, _, take_name, _ = RPR.GetSetMediaItemTakeInfo_String(
                    take, "P_NAME", "", False
                )
                is_midi = bool(RPR.TakeIsMIDI(take))
            items.append(
                {
                    "index": i,
                    "name": take_name,
                    "position": self._time_to_beats(pos),
                    "length": (
                        self._time_to_beats(pos + length) - self._time_to_beats(pos)
                    ),
                    "is_midi": is_midi,
                }
            )

        fx_list = []
        for i in range(RPR.TrackFX_GetCount(track)):
            _, _, _, fx_name, _ = RPR.TrackFX_GetFXName(track, i, "", 256)
            fx_list.append({"index": i, "name": fx_name})

        volume = RPR.GetMediaTrackInfo_Value(track, "D_VOL")
        pan = RPR.GetMediaTrackInfo_Value(track, "D_PAN")
        mute = RPR.GetMediaTrackInfo_Value(track, "B_MUTE") != 0
        solo = RPR.GetMediaTrackInfo_Value(track, "I_SOLO") != 0
        arm = RPR.GetMediaTrackInfo_Value(track, "I_RECARM") != 0

        return {
            "name": name,
            "mute": mute,
            "solo": solo,
            "arm": arm,
            "volume": volume,
            "pan": pan,
            "items": items,
            "fx": fx_list,
        }

    # ── Track Management ──────────────────────────────────────────────

    def _create_track(self, index: int = -1) -> dict[str, Any]:
        RPR = self._api
        count = RPR.CountTracks(0)
        if index == -1:
            index = count
        RPR.InsertTrackAtIndex(index, True)
        track = RPR.GetTrack(0, index)
        _, _, _, name, _ = RPR.GetSetMediaTrackInfo_String(track, "P_NAME", "", False)
        return {"index": index, "name": name}

    def _delete_track(self, track_index: int) -> dict[str, Any]:
        track = self._get_track(track_index)
        self._api.DeleteTrack(track)
        return {"deleted": True}

    def _delete_all_tracks(self) -> dict[str, Any]:
        RPR = self._api
        count = RPR.CountTracks(0)
        for i in range(count - 1, -1, -1):
            track = RPR.GetTrack(0, i)
            RPR.DeleteTrack(track)
        return {"deleted": count, "remaining_tracks": 0}

    def _set_track_name(self, track_index: int, name: str) -> dict[str, Any]:
        track = self._get_track(track_index)
        self._api.GetSetMediaTrackInfo_String(track, "P_NAME", name, True)
        return {"name": name}

    def _set_track_volume(self, track_index: int, volume: float) -> dict[str, Any]:
        RPR = self._api
        track = self._get_track(track_index)
        volume = max(0.0, min(4.0, float(volume)))
        RPR.SetMediaTrackInfo_Value(track, "D_VOL", volume)
        return {"volume": RPR.GetMediaTrackInfo_Value(track, "D_VOL")}

    def _set_track_pan(self, track_index: int, pan: float) -> dict[str, Any]:
        RPR = self._api
        track = self._get_track(track_index)
        pan = max(-1.0, min(1.0, float(pan)))
        RPR.SetMediaTrackInfo_Value(track, "D_PAN", pan)
        return {"pan": RPR.GetMediaTrackInfo_Value(track, "D_PAN")}

    def _set_track_mute(self, track_index: int, mute: bool) -> dict[str, Any]:
        RPR = self._api
        track = self._get_track(track_index)
        RPR.SetMediaTrackInfo_Value(track, "B_MUTE", 1 if mute else 0)
        return {"mute": RPR.GetMediaTrackInfo_Value(track, "B_MUTE") != 0}

    def _set_track_solo(self, track_index: int, solo: bool) -> dict[str, Any]:
        RPR = self._api
        track = self._get_track(track_index)
        RPR.SetMediaTrackInfo_Value(track, "I_SOLO", 1 if solo else 0)
        return {"solo": RPR.GetMediaTrackInfo_Value(track, "I_SOLO") != 0}

    # ── Media Items ───────────────────────────────────────────────────

    def _get_items(self, track_index: int) -> dict[str, Any]:
        RPR = self._api
        track = self._get_track(track_index)
        items = []
        for i in range(RPR.CountTrackMediaItems(track)):
            item = RPR.GetTrackMediaItem(track, i)
            pos = RPR.GetMediaItemInfo_Value(item, "D_POSITION")
            length = RPR.GetMediaItemInfo_Value(item, "D_LENGTH")
            take = RPR.GetActiveTake(item)
            take_name = ""
            is_midi = False
            if take:
                _, _, take_name, _ = RPR.GetSetMediaItemTakeInfo_String(
                    take, "P_NAME", "", False
                )
                is_midi = bool(RPR.TakeIsMIDI(take))
            items.append(
                {
                    "index": i,
                    "name": take_name,
                    "position": self._time_to_beats(pos),
                    "length": (
                        self._time_to_beats(pos + length) - self._time_to_beats(pos)
                    ),
                    "is_midi": is_midi,
                }
            )
        return {"items": items}

    def _create_midi_item(
        self, track_index: int, position: float, length: float = 4.0
    ) -> dict[str, Any]:
        track = self._get_track(track_index)
        start_sec = self._beats_to_time(float(position))
        end_sec = self._beats_to_time(float(position) + float(length))
        self._api.CreateNewMIDIItemInProj(track, start_sec, end_sec, False)
        return {
            "track_index": track_index,
            "position": float(position),
            "length": float(length),
        }

    def _delete_item(self, track_index: int, item_index: int) -> dict[str, Any]:
        track = self._get_track(track_index)
        item = self._get_item(track_index, item_index)
        self._api.DeleteTrackMediaItem(track, item)
        return {"deleted": True}

    def _duplicate_item(
        self, track_index: int, item_index: int, destination_time: float
    ) -> dict[str, Any]:
        RPR = self._api
        item = self._get_item(track_index, item_index)
        dest_sec = self._beats_to_time(float(destination_time))

        RPR.SelectAllMediaItems(0, False)
        RPR.SetMediaItemSelected(item, True)
        RPR.Main_OnCommand(40698, 0)  # Item: Copy items

        RPR.SetEditCurPos(dest_sec, False, False)
        RPR.Main_OnCommand(42398, 0)  # Item: Paste items/tracks

        RPR.SelectAllMediaItems(0, False)

        return {
            "duplicated": True,
            "destination_time": float(destination_time),
        }

    def _set_item_name(
        self, track_index: int, item_index: int, name: str
    ) -> dict[str, Any]:
        take = self._get_active_take(track_index, item_index)
        self._api.GetSetMediaItemTakeInfo_String(take, "P_NAME", name, True)
        return {"name": name}

    # ── MIDI Notes ────────────────────────────────────────────────────

    def _get_item_notes(self, track_index: int, item_index: int) -> dict[str, Any]:
        RPR = self._api
        take = self._get_active_take(track_index, item_index)
        if not RPR.TakeIsMIDI(take):
            raise ValueError("Item does not contain MIDI data")

        _, note_count, _, _ = RPR.MIDI_CountEvts(take, 0, 0, 0)
        notes = []
        for i in range(note_count):
            _, _, _, muted, start_ppq, end_ppq, _chan, pitch, vel = RPR.MIDI_GetNote(
                take, i, False, False, 0, 0, 0, 0, 0
            )
            start_beats = self._ppq_to_beats(take, start_ppq)
            end_beats = self._ppq_to_beats(take, end_ppq)
            notes.append(
                {
                    "pitch": pitch,
                    "start_time": start_beats,
                    "duration": end_beats - start_beats,
                    "velocity": vel,
                    "mute": muted,
                }
            )
        return {"notes": notes}

    def _set_item_notes(
        self,
        track_index: int,
        item_index: int,
        notes: list[dict],
        append: bool = False,
    ) -> dict[str, Any]:
        RPR = self._api
        take = self._get_active_take(track_index, item_index)
        if not RPR.TakeIsMIDI(take):
            raise ValueError("Item does not contain MIDI data")

        if not append:
            _, note_count, _, _ = RPR.MIDI_CountEvts(take, 0, 0, 0)
            for i in range(note_count - 1, -1, -1):
                RPR.MIDI_DeleteNote(take, i)

        for n in notes:
            pitch = int(n.get("pitch", 60))
            start_beats = float(n.get("start_time", 0.0))
            duration = float(n.get("duration", 0.5))
            velocity = int(n.get("velocity", 100))
            muted = bool(n.get("mute", False))

            start_ppq = self._beats_to_ppq(take, start_beats)
            end_ppq = self._beats_to_ppq(take, start_beats + duration)

            RPR.MIDI_InsertNote(
                take,
                False,
                muted,
                start_ppq,
                end_ppq,
                0,
                pitch,
                velocity,
                True,
            )

        RPR.MIDI_Sort(take)
        return {"notes_set": len(notes)}

    # ── Transport ─────────────────────────────────────────────────────

    def _start_playback(self) -> dict[str, Any]:
        self._api.OnPlayButton()
        return {"playing": True}

    def _stop_playback(self) -> dict[str, Any]:
        self._api.OnStopButton()
        return {"playing": False}

    def _set_tempo(self, tempo: float) -> dict[str, Any]:
        RPR = self._api
        tempo = max(1.0, min(960.0, float(tempo)))
        RPR.SetCurrentBPM(0, tempo, True)
        return {"tempo": RPR.Master_GetTempo()}

    def _set_time_signature(self, numerator: int, denominator: int) -> dict[str, Any]:
        RPR = self._api
        num = int(numerator)
        denom = int(denominator)
        RPR.SetTempoTimeSigMarker(
            0, -1, 0.0, -1, -1, RPR.Master_GetTempo(), num, denom, False
        )
        RPR.UpdateTimeline()
        return {
            "signature_numerator": num,
            "signature_denominator": denom,
        }

    def _undo(self) -> dict[str, Any]:
        self._api.Undo_DoUndo2(0)
        return {"undone": True}

    def _set_cursor_position(self, time: float) -> dict[str, Any]:
        RPR = self._api
        time_sec = self._beats_to_time(max(0.0, float(time)))
        RPR.SetEditCurPos(time_sec, True, False)
        return {"cursor_position": self._time_to_beats(RPR.GetCursorPosition())}

    def _get_loop_region(self) -> dict[str, Any]:
        _, _, start_sec, end_sec, _ = self._api.GetSet_LoopTimeRange(
            False, True, 0.0, 0.0, False
        )
        start_beats = self._time_to_beats(start_sec)
        end_beats = self._time_to_beats(end_sec)
        return {
            "loop_start": start_beats,
            "loop_length": end_beats - start_beats,
        }

    def _set_loop_region(self, start: float, length: float) -> dict[str, Any]:
        start_sec = self._beats_to_time(max(0.0, float(start)))
        end_sec = self._beats_to_time(max(0.0, float(start) + float(length)))
        self._api.GetSet_LoopTimeRange(True, True, start_sec, end_sec, False)
        return {
            "loop_start": float(start),
            "loop_length": float(length),
        }

    # ── FX ────────────────────────────────────────────────────────────

    def _add_fx(self, track_index: int, fx_name: str) -> dict[str, Any]:
        RPR = self._api
        track = self._get_track(track_index)
        fx_idx = RPR.TrackFX_AddByName(track, fx_name, False, -1)
        if fx_idx < 0:
            raise ValueError(f"FX not found: {fx_name}")
        _, _, _, resolved_name, _ = RPR.TrackFX_GetFXName(track, fx_idx, "", 256)
        return {"fx_index": fx_idx, "name": resolved_name}

    def _remove_fx(self, track_index: int, fx_index: int) -> dict[str, Any]:
        RPR = self._api
        track = self._get_track(track_index)
        count = RPR.TrackFX_GetCount(track)
        if fx_index < 0 or fx_index >= count:
            raise ValueError(f"FX index {fx_index} out of range (0-{count - 1})")
        RPR.TrackFX_Delete(track, fx_index)
        return {"removed": True}

    def _get_fx_parameters(self, track_index: int, fx_index: int) -> dict[str, Any]:
        RPR = self._api
        track = self._get_track(track_index)
        count = RPR.TrackFX_GetCount(track)
        if fx_index < 0 or fx_index >= count:
            raise ValueError(f"FX index {fx_index} out of range (0-{count - 1})")

        _, _, _, fx_name, _ = RPR.TrackFX_GetFXName(track, fx_index, "", 256)
        num_params = RPR.TrackFX_GetNumParams(track, fx_index)
        params = []
        for i in range(num_params):
            _, _, _, _, p_name, _ = RPR.TrackFX_GetParamName(
                track, fx_index, i, "", 256
            )
            val, min_val, max_val = RPR.TrackFX_GetParam(track, fx_index, i, 0, 0)[1:]
            params.append(
                {
                    "index": i,
                    "name": p_name,
                    "value": val,
                    "min": min_val,
                    "max": max_val,
                }
            )
        return {"fx_name": fx_name, "parameters": params}

    def _set_fx_parameter(
        self,
        track_index: int,
        fx_index: int,
        param_index: int,
        value: float,
    ) -> dict[str, Any]:
        RPR = self._api
        track = self._get_track(track_index)
        count = RPR.TrackFX_GetCount(track)
        if fx_index < 0 or fx_index >= count:
            raise ValueError(f"FX index {fx_index} out of range (0-{count - 1})")
        num_params = RPR.TrackFX_GetNumParams(track, fx_index)
        if param_index < 0 or param_index >= num_params:
            raise ValueError(
                f"Parameter index {param_index} out of range" f" (0-{num_params - 1})"
            )
        _, min_val, max_val = RPR.TrackFX_GetParam(track, fx_index, param_index, 0, 0)[
            1:
        ]
        clamped = max(min_val, min(max_val, float(value)))
        RPR.TrackFX_SetParam(track, fx_index, param_index, clamped)
        _, _, _, _, p_name, _ = RPR.TrackFX_GetParamName(
            track, fx_index, param_index, "", 256
        )
        return {"name": p_name, "value": clamped}

    def _create_track_with_fx(
        self,
        fx_name: str,
        index: int = -1,
        name: str | None = None,
    ) -> dict[str, Any]:
        RPR = self._api
        count = RPR.CountTracks(0)
        if index == -1:
            index = count
        RPR.InsertTrackAtIndex(index, True)
        track = RPR.GetTrack(0, index)

        if name:
            RPR.GetSetMediaTrackInfo_String(track, "P_NAME", name, True)

        fx_idx = RPR.TrackFX_AddByName(track, fx_name, False, -1)
        if fx_idx < 0:
            raise ValueError(f"FX not found: {fx_name}")

        _, _, _, resolved_name, _ = RPR.TrackFX_GetFXName(track, fx_idx, "", 256)
        _, _, _, track_name, _ = RPR.GetSetMediaTrackInfo_String(
            track, "P_NAME", "", False
        )

        return {
            "track_index": index,
            "name": track_name,
            "fx_name": resolved_name,
        }

    # ── Markers / Regions ─────────────────────────────────────────────

    def _add_marker(self, position: float, name: str = "") -> dict[str, Any]:
        pos_sec = self._beats_to_time(float(position))
        idx = self._api.AddProjectMarker(0, False, pos_sec, 0, name, -1)
        return {
            "marker_index": idx,
            "position": float(position),
            "name": name,
        }

    def _add_region(self, start: float, end: float, name: str = "") -> dict[str, Any]:
        start_sec = self._beats_to_time(float(start))
        end_sec = self._beats_to_time(float(end))
        idx = self._api.AddProjectMarker(0, True, start_sec, end_sec, name, -1)
        return {
            "region_index": idx,
            "start": float(start),
            "end": float(end),
            "name": name,
        }

    def _get_markers(self) -> dict[str, Any]:
        RPR = self._api
        _, num_markers, num_regions = RPR.CountProjectMarkers(0, 0, 0)
        total = num_markers + num_regions
        markers: list[dict[str, Any]] = []
        regions: list[dict[str, Any]] = []
        for i in range(total):
            _, _, is_rgn, pos_sec, rgn_end_sec, name, idx = RPR.EnumProjectMarkers(
                i, False, 0.0, 0.0, "", 0
            )
            if is_rgn:
                regions.append(
                    {
                        "index": idx,
                        "name": name,
                        "start": self._time_to_beats(pos_sec),
                        "end": self._time_to_beats(rgn_end_sec),
                    }
                )
            else:
                markers.append(
                    {
                        "index": idx,
                        "name": name,
                        "position": self._time_to_beats(pos_sec),
                    }
                )
        return {"markers": markers, "regions": regions}
