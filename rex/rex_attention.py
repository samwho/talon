import json

from .rex_client import Rex, RexError
from .rex_terminal import focused_session_view


def focus_next_waiting(rex: Rex, app_pid: int) -> None:
    """Cycle to another done or blocked terminal in the visible session."""
    view = focused_session_view(rex, app_pid)
    session = view["session_id"]
    windows = view.get("windows") or []
    active = next(
        (w for w in windows if w["window_id"] == view.get("active_window_id")), None
    )
    if active is None:
        raise RexError("Rex has no active window")
    # Keep non-terminal blocks in the ordering so they can be the current
    # position, but never query program_status on them.
    blocks = [
        (window["window_id"], block)
        for window in windows
        for layer in window.get("layers", [])
        for block in layer.get("blocks", [])
    ]
    current = next(
        (
            index
            for index, (window_id, block) in enumerate(blocks)
            if window_id == active["window_id"]
            and block["block_id"] == active.get("focused_block_id")
        ),
        None,
    )
    if current is None:
        raise RexError("Cannot identify Rex's focused block")
    for distance in range(1, len(blocks)):
        window_id, block = blocks[(current + distance) % len(blocks)]
        if block.get("creator_name") != "com.superlogical.terminal":
            continue
        status = rex.call(
            "block", "call", "-s", session, "-b", block["block_id"], "program_status"
        )
        if not any(
            record.get("state") in {"done", "blocked"}
            for record in status.get("records", [])
        ):
            continue
        rex.call(
            "api",
            "call",
            "session.focus_block",
            json.dumps({"session_id": session, "block_id": block["block_id"]}),
        )
        rex.perform_action(
            "session.select", {"session_id": session, "window_id": window_id}
        )
        return
    raise RexError("No other done or blocked terminals in the current Rex session")
