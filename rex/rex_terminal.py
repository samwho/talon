import os
from typing import Any

from .rex_client import Rex, RexError

# A process name alone is not enough to enable shell commands: an interpreter
# may be running a script, or a shell may be hosting a full-screen application.
_SHELLS = {"bash", "zsh", "fish", "sh", "dash", "ksh", "tcsh", "csh", "nu", "nushell"}


def process_program(process: dict[str, Any]) -> str:
    """Prefer Rex's script/argv0 identity, so node running Pi becomes pi."""
    value = process.get("script") or process.get("argv0") or process.get("name")
    return os.path.basename(str(value or "")).lstrip("-") or "unknown"


def focused_session_view(rex: Rex, app_pid: int) -> dict[str, Any]:
    """Read the local app's session, failing closed on ambiguous focus.

    Rex does not expose which attached session a client is viewing. Only use
    its session attachment when there is exactly one; never guess from the
    inherited REX_SESSION or from the first session on the server.
    """
    if rex.client:
        client = rex.call("client", "inspect", rex.client, "--json")["client"]
        clients = [client]
    else:
        clients = rex.call("client", "ls", "--json")["clients"]
    clients = [
        client
        for client in clients
        if client.get("info", {}).get("kind") == "app"
        and client.get("principal", {}).get("transport") == "unix"
        and client.get("principal", {}).get("pid") == app_pid
        and client.get("connection_state", "connected") == "connected"
    ]
    if len(clients) != 1:
        raise RexError("Cannot identify the active local Rex client")
    sessions = clients[0].get("session_ids") or []
    if len(sessions) != 1:
        raise RexError("Cannot identify Rex's visible session: expected one attachment")
    session = sessions[0]
    return rex.call("session", "inspect", session, "--json")


def terminal_snapshot(rex: Rex, app_pid: int) -> dict[str, str]:
    """Read the local app's focused terminal metadata."""
    view = focused_session_view(rex, app_pid)
    session = view["session_id"]
    windows = view.get("windows") or []
    window = next(
        (w for w in windows if w["window_id"] == view.get("active_window_id")), None
    )
    if window is None:
        raise RexError("Rex has no active window")
    block_id = window.get("focused_block_id")
    blocks = [
        block for layer in window.get("layers", []) for block in layer.get("blocks", [])
    ]
    block = next((b for b in blocks if b["block_id"] == block_id), None)
    if block is None or block.get("creator_name") != "com.superlogical.terminal":
        raise RexError("The focused Rex pane is not a terminal")

    def block_call(method: str) -> dict[str, Any]:
        return rex.call("block", "call", "-s", session, "-b", block_id, method)

    info = block_call("process")
    foreground = info.get("foreground") or {}
    program = process_program(foreground)
    screen = block_call("modes").get("screen")
    if program in _SHELLS and (screen != "primary" or foreground.get("script")):
        program = "unknown"
    # File-manager pickers enumerate paths using Talon's local filesystem.
    # A remote terminal's /Users/... or /home/... must never be treated as local.
    status = rex.call("api", "call", "server.status", "{}")
    local = bool(block.get("host_id")) and block["host_id"] == status.get("host_id")
    cwd = foreground.get("cwd") if local else None
    title = block_call("title").get("title") or block.get("label") or "unknown"
    return {
        "title": str(title),
        "cwd": str(cwd or "none"),
        "terminal_id": str(block_id),
        "window_id": str(window["window_id"]),
        "window_title": str(window.get("label") or "none"),
        "tab_id": str(window["window_id"]),
        "tab_name": str(window.get("label") or "none"),
        "tab_index": str(windows.index(window) + 1),
        "command": program,
    }
