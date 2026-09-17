import json
import os
import queue
import shlex
import shutil
import subprocess
import threading
from typing import Any

from talon import Context, Module, cron, ui

mod = Module()
mod.apps.samwho_terminal = r"""
os: mac
and app.bundle: com.mitchellh.ghostty
"""

_GHOSTTY_BUNDLE = "com.mitchellh.ghostty"
_TERMINAL_BUNDLES = {_GHOSTTY_BUNDLE}
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

_state_lock = threading.Lock()
_refresh_lock = threading.Lock()
_refresh_job = None
_refresh_running = False
_refresh_revision = 0
_refresh_worker_started = False
_refresh_queue: queue.Queue[int] = queue.Queue(maxsize=1)
_current_scope = {key: _NONE for key in _SCOPE_KEYS}


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


def _herdr_path() -> str | None:
    """Find Herdr even when Talon's PATH does not include Homebrew."""
    candidates = [
        shutil.which("herdr"),
        "/opt/homebrew/bin/herdr",
        "/usr/local/bin/herdr",
    ]
    for candidate in candidates:
        if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


def _run(command: list[str], timeout: float = 0.75) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _ghostty_terminal() -> dict[str, str] | None:
    """Return metadata for Ghostty's front window, selected tab, and focused terminal."""
    active_app = ui.active_app()
    if not active_app or active_app.bundle != _GHOSTTY_BUNDLE:
        return None

    try:
        ghostty = active_app.appscript()
        if not ghostty.frontmost():
            return None
        window = ghostty.front_window()
        tab = window.selected_tab()
        terminal = tab.focused_terminal()
        result = {
            "title": _scope_text(terminal.name()),
            "cwd": _scope_text(terminal.working_directory()),
            "terminal_id": _scope_text(terminal.id()),
            "window_id": _scope_text(window.id()),
            "window_title": _scope_text(window.name()),
            "tab_id": _scope_text(tab.id()),
            "tab_name": _scope_text(tab.name()),
            "tab_index": _scope_text(tab.index()),
            "command": _scope_text(terminal.name()),
        }
    except Exception as error:
        raise RuntimeError(f"Ghostty AppleScript query failed: {error}") from error

    if result["title"] == _NONE:
        raise RuntimeError("Ghostty returned an empty terminal title")
    return result


def _active_terminal() -> dict[str, str] | None:
    """Return metadata for the active Ghostty terminal."""
    active_app = ui.active_app()
    if not active_app or active_app.bundle != _GHOSTTY_BUNDLE:
        return None
    return _ghostty_terminal()


def _herdr_scope_values(herdr: str) -> dict[str, str] | None:
    """Return metadata for the pane focused in the active Herdr client."""
    pane_result = _run([herdr, "pane", "current"])
    if pane_result.returncode != 0:
        return None
    try:
        response = json.loads(pane_result.stdout)
        pane = response["result"]["pane"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return None
    if not isinstance(pane, dict):
        return None

    pane_id = pane.get("pane_id")
    if not pane_id:
        return None

    agent = pane.get("agent")
    command = agent
    if not agent:
        process_result = _run([herdr, "pane", "process-info", "--pane", pane_id])
        if process_result.returncode == 0:
            try:
                process_response = json.loads(process_result.stdout)
                process_info = process_response["result"]["process_info"]
                process_group = process_info.get("foreground_process_group_id")
                processes = process_info.get("foreground_processes", [])
                foreground = [
                    process
                    for process in processes
                    if process.get("pid") == process_group
                ]
                if len(foreground) == 1:
                    process = foreground[0]
                    command = process.get("cmdline") or process.get("argv0")
            except (json.JSONDecodeError, KeyError, TypeError):
                pass

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
    scope = {key: _NONE for key in _SCOPE_KEYS}
    terminal = _active_terminal()
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

    # Herdr's configured window-title template starts with a stable marker and
    # includes workspace/tab/pane data, so Ghostty emits a title event whenever
    # the focused virtual pane changes.
    is_herdr = native_command.lower().startswith("herdr | ")
    if is_herdr:
        scope["terminal_program"] = "herdr"
        scope["terminal_command"] = native_command
        scope["terminal_is_herdr"] = "true"
        herdr = _herdr_path()
        herdr_values = _herdr_scope_values(herdr) if herdr else None
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
    with _state_lock:
        return dict(_current_scope)


def _publish(new_scope: dict[str, str]) -> None:
    global _current_scope
    with _state_lock:
        if new_scope == _current_scope:
            return
        _current_scope = new_scope

    print(
        "user.terminal_program = "
        f"{new_scope['terminal_program']}; "
        f"user.terminal_focused_program = {new_scope['terminal_focused_program']}; "
        f"user.herdr_program = {new_scope['herdr_program']}"
    )
    cron.after("0ms", samwho_terminal_scope.update)


def _refresh_worker_loop() -> None:
    while True:
        revision = _refresh_queue.get()
        try:
            new_scope = _detect_scope()
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
            print(f"terminal program query failed: {error}")
            new_scope = {key: _NONE for key in _SCOPE_KEYS}
            new_scope["terminal_program"] = _UNKNOWN
            new_scope["terminal_is_herdr"] = _UNKNOWN

        # Keep scope publication in Talon's managed callback thread; all
        # AppleScript/subprocess work happened on this long-lived worker.
        cron.after(
            "0ms",
            lambda revision=revision, new_scope=new_scope: _finish_poll(
                revision, new_scope
            ),
        )


def _ensure_refresh_worker() -> None:
    global _refresh_worker_started
    with _refresh_lock:
        if _refresh_worker_started:
            return
        _refresh_worker_started = True

    threading.Thread(
        target=_refresh_worker_loop,
        daemon=True,
        name="terminal-scope-refresh",
    ).start()


def _queue_refresh(revision: int) -> None:
    try:
        _refresh_queue.put_nowait(revision)
    except queue.Full:
        # The worker is already handling the newest queued refresh.
        pass


def _start_poll() -> None:
    global _refresh_job, _refresh_running
    _refresh_job = None
    with _refresh_lock:
        if _refresh_running:
            return
        _refresh_running = True
        revision = _refresh_revision

    _ensure_refresh_worker()
    _queue_refresh(revision)


def _finish_poll(revision: int, new_scope: dict[str, str]) -> None:
    global _refresh_running
    with _refresh_lock:
        current_revision = _refresh_revision
        if revision == current_revision:
            _refresh_running = False
            next_revision = None
        else:
            # A UI event arrived while this query was running. Discard its
            # stale result and immediately refresh the newest surface state.
            next_revision = current_revision

    if next_revision is not None:
        _queue_refresh(next_revision)
        return

    _publish(new_scope)


def _schedule_poll(*_args: object) -> None:
    """Debounce terminal UI events before a background metadata query."""
    global _refresh_job, _refresh_revision

    # Window-title events are global. Ignore unrelated applications unless the
    # last published scope still contains terminal data that needs clearing.
    try:
        active_app = ui.active_app()
        terminal_active = active_app is not None and active_app.bundle in _TERMINAL_BUNDLES
    except (AttributeError, RuntimeError, ui.UIErr):
        terminal_active = True
    if not terminal_active:
        with _state_lock:
            has_stale_terminal_scope = _current_scope["terminal_program"] != _NONE
        if not has_stale_terminal_scope:
            return

    with _refresh_lock:
        _refresh_revision += 1
    if _refresh_job is not None:
        cron.cancel(_refresh_job)
    _refresh_job = cron.after("50ms", _start_poll)


# Talon reports application/window activation and title changes. Both supported
# terminals update their visible title as focus changes. Herdr's configured
# title includes its virtual pane, so these events cover all supported nesting
# without a standing timer.
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
        with _state_lock:
            if _current_scope["terminal_is_herdr"] == "true":
                path = _current_scope["herdr_cwd"]
                if path in (_NONE, _UNKNOWN):
                    path = _current_scope["terminal_cwd"]
            else:
                path = _current_scope["terminal_cwd"]

        if path in (_NONE, _UNKNOWN):
            raise RuntimeError("Terminal did not report the current directory")
        return path


cron.after("0ms", _start_poll)
