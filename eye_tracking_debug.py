"""Short, opt-in recordings of Talon's raw Tobii gaze frames.

This uses Talon's internal eye-tracker API because the public tracking actions do
not expose per-eye validity. Recordings are written to ~/.talon/eye-debug/.
"""

import csv
from datetime import datetime
from pathlib import Path
import time

from talon import Module, actions, cron, tracking_system
from talon.plugins import eye_mouse, eye_zoom_mouse

mod = Module()

_OUTPUT_DIR = Path.home() / ".talon" / "eye-debug"
_FIELDS = [
    "event",
    "wall_time",
    "frame_ts",
    "frame_num",
    "combined_x",
    "combined_y",
    "left_detected",
    "left_validity",
    "left_pupil",
    "left_gaze_x",
    "left_gaze_y",
    "left_pos_x",
    "left_pos_y",
    "left_pos_z",
    "right_detected",
    "right_validity",
    "right_pupil",
    "right_gaze_x",
    "right_gaze_y",
    "right_pos_x",
    "right_pos_y",
    "right_pos_z",
    "left_right_distance",
    "zoom_gaze_x",
    "zoom_gaze_y",
    "zoom_state",
]

_tracker = None
_file = None
_writer = None
_path = None
_flush_job = None
_last_frame = None
_last_zoom_state = None
_counts = None


def _point_value(point, axis):
    return getattr(point, axis, "") if point is not None else ""


def _eye_usable(eye):
    # Talon emits validity=4, pupil=-1 and gaze=(0, 0) when an eye has no
    # usable gaze point. Preserve the raw validity in the CSV for finer analysis.
    return eye is not None and eye.validity < 4 and eye.pupil >= 0


def _row(event, frame):
    left = frame.left
    right = frame.right
    left_usable = _eye_usable(left)
    right_usable = _eye_usable(right)

    distance = ""
    if left_usable and right_usable:
        dx = left.gaze.x - right.gaze.x
        dy = left.gaze.y - right.gaze.y
        distance = (dx * dx + dy * dy) ** 0.5

    zoom_gaze = getattr(eye_zoom_mouse.zoom_mouse, "gaze", None)
    return {
        "event": event,
        "wall_time": time.time(),
        "frame_ts": frame.ts,
        "frame_num": frame.num,
        "combined_x": frame.gaze.x,
        "combined_y": frame.gaze.y,
        "left_detected": left.detected,
        "left_validity": left.validity,
        "left_pupil": left.pupil,
        "left_gaze_x": left.gaze.x,
        "left_gaze_y": left.gaze.y,
        "left_pos_x": left.pos.x,
        "left_pos_y": left.pos.y,
        "left_pos_z": left.pos.z,
        "right_detected": right.detected,
        "right_validity": right.validity,
        "right_pupil": right.pupil,
        "right_gaze_x": right.gaze.x,
        "right_gaze_y": right.gaze.y,
        "right_pos_x": right.pos.x,
        "right_pos_y": right.pos.y,
        "right_pos_z": right.pos.z,
        "left_right_distance": distance,
        "zoom_gaze_x": _point_value(zoom_gaze, "x"),
        "zoom_gaze_y": _point_value(zoom_gaze, "y"),
        "zoom_state": getattr(eye_zoom_mouse.zoom_mouse, "state", ""),
    }


def _on_gaze(frame):
    global _last_frame, _last_zoom_state
    _last_frame = frame
    if _writer is None:
        return

    left_usable = _eye_usable(frame.left)
    right_usable = _eye_usable(frame.right)
    if left_usable and right_usable:
        _counts["both"] += 1
    elif left_usable:
        _counts["left_only"] += 1
    elif right_usable:
        _counts["right_only"] += 1
    else:
        _counts["neither"] += 1
    _counts["frames"] += 1

    zoom_state = getattr(eye_zoom_mouse.zoom_mouse, "state", 0)
    event = "gaze"
    if zoom_state == 1 and _last_zoom_state != 1:
        event = "pop"
        _counts["pops"] += 1
        print(f"Eye debug: detected zoom pop in {_path}")
    _last_zoom_state = zoom_state
    _writer.writerow(_row(event, frame))


def _flush():
    if _file is not None:
        _file.flush()


def _summary():
    if not _counts:
        return "Eye debug is not recording"
    frames = _counts["frames"]
    if not frames:
        return "Eye debug recording has no gaze frames"

    def percent(key):
        return 100 * _counts[key] / frames

    return (
        f"{frames} frames, {_counts['pops']} pops; "
        f"both {percent('both'):.1f}%, left only {percent('left_only'):.1f}%, "
        f"right only {percent('right_only'):.1f}%, neither {percent('neither'):.1f}%"
    )


def _start():
    global _tracker, _file, _writer, _path, _flush_job, _last_zoom_state, _counts
    if _writer is not None:
        actions.app.notify("Eye debug", "Already recording")
        return

    tracker = eye_mouse.tracker
    if tracker is None:
        actions.app.notify("Eye debug", "No Tobii tracker connected")
        return

    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    _path = _OUTPUT_DIR / f"gaze-{stamp}.csv"
    _file = _path.open("w", newline="")
    _writer = csv.DictWriter(_file, fieldnames=_FIELDS)
    _writer.writeheader()
    _counts = {
        "frames": 0,
        "pops": 0,
        "both": 0,
        "left_only": 0,
        "right_only": 0,
        "neither": 0,
    }
    _tracker = tracker
    _last_zoom_state = getattr(eye_zoom_mouse.zoom_mouse, "state", 0)
    tracking_system.register("gaze", _on_gaze)
    _flush_job = cron.interval("1s", _flush)
    actions.app.notify("Eye debug", f"Recording to {_path.name}")
    print(f"Eye debug: recording to {_path}")


def _stop():
    global _tracker, _file, _writer, _flush_job
    if _writer is None:
        actions.app.notify("Eye debug", "Not recording")
        return

    if _tracker is not None:
        tracking_system.unregister("gaze", _on_gaze)
    cron.cancel(_flush_job)
    summary = _summary()
    path = _path
    _file.flush()
    _file.close()
    _tracker = None
    _file = None
    _writer = None
    _flush_job = None
    actions.app.notify("Eye debug stopped", summary)
    print(f"Eye debug: {summary}; saved {path}")


@mod.action_class
class Actions:
    def samwho_eye_debug_start() -> None:
        """Start recording raw per-eye Tobii gaze data and pop markers."""
        _start()

    def samwho_eye_debug_stop() -> None:
        """Stop recording raw Tobii gaze data and print a summary."""
        _stop()

    def samwho_eye_debug_status() -> None:
        """Show statistics for the current Tobii gaze recording."""
        actions.app.notify("Eye debug", _summary())

    def samwho_eye_debug_mark() -> None:
        """Add a manual marker to the current Tobii gaze recording."""
        if _writer is not None and _last_frame is not None:
            _writer.writerow(_row("manual", _last_frame))
            _file.flush()
