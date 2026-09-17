import json
import os
import shlex
import threading
from typing import Any

from talon import Context, Module, cron, ui

from ..ghostty.ghostty_client import GHOSTTY_BUNDLE, snapshot as ghostty_snapshot
from ..herdr.herdr_client import HerdrError, current_pane, process_info
from .latest_refresh import LatestOnlyRefresh

mod = Module()
mod.apps.samwho_terminal = f"""
os: mac
and app.bundle: {GHOSTTY_BUNDLE}
"""

_TERMINAL_BUNDLES = {GHOSTTY_BUNDLE}
_UNKNOWN = "unknown"
_NONE = "none"

# All scope values are strings so they can be used directly in .talon context
# headers. Values are deliberately present as "none" when their source is not
# active, which clears stale Herdr data when switching to a native terminal.
# `terminal_focused_program` normalizes native and Herdr programs while
# `terminal_program` retains the host process identity.
_SCOPE_KEYS = {
    "terminal_program",
    "terminal_focused_program",
    "terminal_command",
    "terminal_title",
    "terminal_cwd",
    "terminal_id",
    "terminal_window_id",
    "terminal_window_title",
    "terminal_tab_id",
    "terminal_tab_name",
    "terminal_tab_index",
    "terminal_is_herdr",
    "herdr_workspace_id",
    "herdr_tab_id",
    "herdr_pane_id",
    "herdr_terminal_id",
    "herdr_program",
    "herdr_command",
    "herdr_title",
    "herdr_cwd",
    "herdr_agent",
    "herdr_agent_status",
}


def _empty_scope() -> dict[str, str]:
    return {key: _NONE for key in _SCOPE_KEYS}


class TerminalScopeStore:
    """Thread-safe storage for the currently published terminal scope."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._scope = _empty_scope()

    def snapshot(self) -> dict[str, str]:
        with self._lock:
            return dict(self._scope)

    def has_terminal_data(self) -> bool:
        with self._lock:
            return self._scope["terminal_program"] != _NONE

    def publish(self, scope: dict[str, str]) -> bool:
        with self._lock:
            if scope == self._scope:
                return False
            self._scope = scope
            return True


_scope_store = TerminalScopeStore()


def _scope_text(value: Any) -> str:
    """Convert JSON/Appscript values to useful string-valued scope data."""
    if value is None:
        return _NONE
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    text = str(value).strip()
    return text or _NONE


def _ghostty_terminal() -> dict[str, str] | None:
    """Return metadata for Ghostty's focused terminal."""
    terminal = ghostty_snapshot()
    if terminal is None:
        return None

    result = {
        "title": _scope_text(terminal.title),
        "cwd": _scope_text(terminal.cwd),
        "terminal_id": _scope_text(terminal.terminal_id),
        "window_id": _scope_text(terminal.window_id),
        "window_title": _scope_text(terminal.window_title),
        "tab_id": _scope_text(terminal.tab_id),
        "tab_name": _scope_text(terminal.tab_name),
        "tab_index": _scope_text(terminal.tab_index),
        "command": _scope_text(terminal.title),
    }
    if result["title"] == _NONE:
        raise RuntimeError("Ghostty returned an empty terminal title")
    return result


def _herdr_scope_values() -> dict[str, str] | None:
    """Return metadata for the pane focused in the active Herdr client."""
    try:
        pane = current_pane()
    except HerdrError:
        return None

    pane_id = pane.get("pane_id")
    if not pane_id:
        return None

    agent = pane.get("agent")
    command = agent
    if not agent:
        try:
            info = process_info(str(pane_id))
        except HerdrError:
            info = None
        if info is not None:
            process_group = info.get("foreground_process_group_id")
            processes = info.get("foreground_processes", [])
            foreground = [
                process
                for process in processes
                if process.get("pid") == process_group
            ]
            if len(foreground) == 1:
                process = foreground[0]
                command = process.get("cmdline") or process.get("argv0")

    program = _scope_text(agent) if agent else _program_name(command)
    return {
        "herdr_workspace_id": _scope_text(pane.get("workspace_id")),
        "herdr_tab_id": _scope_text(pane.get("tab_id")),
        "herdr_pane_id": _scope_text(pane_id),
        "herdr_terminal_id": _scope_text(pane.get("terminal_id")),
        "herdr_program": program,
        "herdr_command": _scope_text(command),
        "herdr_title": _scope_text(
            pane.get("title") or pane.get("terminal_title_stripped")
        ),
        "herdr_cwd": _scope_text(pane.get("foreground_cwd") or pane.get("cwd")),
        "herdr_agent": _scope_text(agent),
        "herdr_agent_status": _scope_text(pane.get("agent_status")),
    }


def _program_name(command_or_title: Any) -> str:
    """Reduce a command or title to an executable-like scope value."""
    value = str(command_or_title or "").strip()
    if not value:
        return _UNKNOWN

    try:
        parts = shlex.split(value)
    except ValueError:
        parts = value.split()
    if not parts:
        return _UNKNOWN

    # Login shells conventionally prefix argv[0] with a hyphen.
    program = os.path.basename(parts[0]).lstrip("-")
    # GUI terminal launchers commonly invoke scripts through a shell.
    if program in {"bash", "zsh", "sh", "dash", "ksh"} and len(parts) > 1:
        script = os.path.basename(parts[1])
        if script and not script.startswith("-"):
            return script
    return program or _UNKNOWN


def _detect_scope() -> dict[str, str]:
    scope = _empty_scope()
    terminal = _ghostty_terminal()
    if terminal is None:
        return scope

    scope.update(
        {
            "terminal_title": terminal["title"],
            "terminal_cwd": terminal["cwd"],
            "terminal_id": terminal["terminal_id"],
            "terminal_window_id": terminal["window_id"],
            "terminal_window_title": terminal["window_title"],
            "terminal_tab_id": terminal["tab_id"],
            "terminal_tab_name": terminal["tab_name"],
            "terminal_tab_index": terminal["tab_index"],
        }
    )

    native_program = _program_name(terminal["command"])
    native_command = terminal["command"]

    # Herdr's configured title starts with a stable marker and changes whenever
    # its focused virtual pane changes.
    is_herdr = native_command.lower().startswith("herdr | ")
    if is_herdr:
        scope["terminal_program"] = "herdr"
        scope["terminal_command"] = native_command
        scope["terminal_is_herdr"] = "true"
        herdr_values = _herdr_scope_values()
        if herdr_values is None:
            scope["terminal_focused_program"] = _UNKNOWN
            scope["herdr_program"] = _UNKNOWN
        else:
            scope.update(herdr_values)
            scope["terminal_focused_program"] = scope["herdr_program"]
        return scope

    scope["terminal_program"] = native_program
    scope["terminal_focused_program"] = native_program
    scope["terminal_command"] = native_command
    scope["terminal_is_herdr"] = "false"
    return scope


@mod.scope
def samwho_terminal_scope() -> dict[str, str]:
    """Expose terminal and nested Herdr metadata as user.* scopes."""
    return _scope_store.snapshot()


def _publish(new_scope: dict[str, str]) -> None:
    if not _scope_store.publish(new_scope):
        return

    print(
        "user.terminal_program = "
        f"{new_scope['terminal_program']}; "
        f"user.terminal_focused_program = {new_scope['terminal_focused_program']}; "
        f"user.herdr_program = {new_scope['herdr_program']}"
    )
    cron.after("0ms", samwho_terminal_scope.update)


def _error_scope(error: Exception) -> dict[str, str]:
    print(f"terminal program query failed: {error}")
    scope = _empty_scope()
    scope["terminal_program"] = _UNKNOWN
    scope["terminal_is_herdr"] = _UNKNOWN
    return scope


_refresh = LatestOnlyRefresh(
    delay="50ms",
    query=_detect_scope,
    publish=_publish,
    on_error=_error_scope,
)


def _schedule_poll(*_args: object) -> None:
    """Debounce terminal UI events before a background metadata query."""
    # Window-title events are global. Ignore unrelated applications unless the
    # last published scope still contains terminal data that needs clearing.
    try:
        active_app = ui.active_app()
        terminal_active = (
            active_app is not None and active_app.bundle in _TERMINAL_BUNDLES
        )
    except (AttributeError, RuntimeError, ui.UIErr):
        terminal_active = True
    if not terminal_active and not _scope_store.has_terminal_data():
        return

    _refresh.request()


# Ghostty updates its visible title as focus changes. Herdr's configured title
# includes its virtual pane, so these events cover supported nesting without a
# standing timer.
ui.register("app_activate", _schedule_poll)
ui.register("app_deactivate", _schedule_poll)
ui.register("win_focus", _schedule_poll)
ui.register("win_title", _schedule_poll)


terminal_ctx = Context()
terminal_ctx.matches = """
app: samwho_terminal
"""


@terminal_ctx.action_class("user")
class TerminalFileManagerActions:
    def file_manager_current_path() -> str:
        scope = _scope_store.snapshot()
        if scope["terminal_is_herdr"] == "true":
            path = scope["herdr_cwd"]
            if path in (_NONE, _UNKNOWN):
                path = scope["terminal_cwd"]
        else:
            path = scope["terminal_cwd"]

        if path in (_NONE, _UNKNOWN):
            raise RuntimeError("Terminal did not report the current directory")
        return path


cron.after("0ms", _refresh.run_now)
