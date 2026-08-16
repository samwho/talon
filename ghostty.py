import json
import os
import queue
import re
import shlex
import shutil
import subprocess
import threading
from typing import Any
from urllib.parse import unquote, urlparse

from talon import Context, Module, actions, cron, ui

mod = Module()
mod.apps.samwho_ghostty = """
os: mac
and app.bundle: com.mitchellh.ghostty
"""
mod.apps.samwho_terminal = r"""
os: mac
and app.bundle: /^(com\.mitchellh\.ghostty|com\.github\.wez\.wezterm)$/
"""

_GHOSTTY_BUNDLE = "com.mitchellh.ghostty"
_WEZTERM_BUNDLE = "com.github.wez.wezterm"
_TERMINAL_BUNDLES = {_GHOSTTY_BUNDLE, _WEZTERM_BUNDLE}
_UNKNOWN = "unknown"
_NONE = "none"

# All scope values are strings so they can be used directly in .talon context
# headers. Values are deliberately present as "none" when their source is not
# active, which clears stale zellij data when switching to a native terminal.
# `terminal_focused_program` normalizes native and nested-Zellij programs for
# app contexts while `terminal_program` retains the host process identity.
_PANE_SCOPE_FIELDS = {
    "is_focused": "zellij_pane_focused",
    "is_fullscreen": "zellij_pane_fullscreen",
    "is_floating": "zellij_pane_floating",
    "is_suppressed": "zellij_pane_suppressed",
    "exited": "zellij_pane_exited",
    "exit_status": "zellij_pane_exit_status",
    "is_held": "zellij_pane_held",
    "pane_x": "zellij_pane_x",
    "pane_content_x": "zellij_pane_content_x",
    "pane_y": "zellij_pane_y",
    "pane_content_y": "zellij_pane_content_y",
    "pane_rows": "zellij_pane_rows",
    "pane_content_rows": "zellij_pane_content_rows",
    "pane_columns": "zellij_pane_columns",
    "pane_content_columns": "zellij_pane_content_columns",
    "cursor_coordinates_in_pane": "zellij_pane_cursor_coordinates",
    "terminal_command": "zellij_terminal_command",
    "plugin_url": "zellij_plugin_url",
    "is_selectable": "zellij_pane_selectable",
    "index_in_pane_group": "zellij_pane_index_in_group",
    "default_fg": "zellij_pane_default_fg",
    "default_bg": "zellij_pane_default_bg",
}

_TAB_SCOPE_FIELDS = {
    "position": "zellij_tab_position",
    "name": "zellij_tab_name",
    "tab_id": "zellij_tab_id",
    "active": "zellij_tab_active",
    "panes_to_hide": "zellij_tab_panes_to_hide",
    "is_fullscreen_active": "zellij_tab_fullscreen",
    "is_sync_panes_active": "zellij_tab_sync_panes",
    "are_floating_panes_visible": "zellij_tab_floating_visible",
    "other_focused_clients": "zellij_tab_other_focused_clients",
    "active_swap_layout_name": "zellij_tab_swap_layout",
    "is_swap_layout_dirty": "zellij_tab_layout_dirty",
    "viewport_rows": "zellij_tab_viewport_rows",
    "viewport_columns": "zellij_tab_viewport_columns",
    "display_area_rows": "zellij_tab_display_area_rows",
    "display_area_columns": "zellij_tab_display_area_columns",
    "selectable_tiled_panes_count": "zellij_tab_tiled_panes",
    "selectable_floating_panes_count": "zellij_tab_floating_panes",
    "has_bell_notification": "zellij_tab_bell",
    "is_flashing_bell": "zellij_tab_flashing_bell",
}

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
    "terminal_is_zellij",
    "zellij_session",
    "zellij_program",
    "zellij_command",
    "zellij_title",
    "zellij_cwd",
    "zellij_pane_id",
    "zellij_pane_numeric_id",
    "zellij_pane_type",
    *_PANE_SCOPE_FIELDS.values(),
    *_TAB_SCOPE_FIELDS.values(),
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


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _wezterm_path() -> str | None:
    """Find WezTerm's CLI even when Talon's PATH does not include Homebrew."""
    candidates = [
        shutil.which("wezterm"),
        "/opt/homebrew/bin/wezterm",
        "/usr/local/bin/wezterm",
    ]
    for candidate in candidates:
        if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


def _zellij_path() -> str | None:
    """Find zellij even when Talon's PATH does not include Homebrew."""
    candidates = [
        shutil.which("zellij"),
        "/opt/homebrew/bin/zellij",
        "/usr/local/bin/zellij",
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


def _wezterm_terminal() -> dict[str, str] | None:
    """Return focused WezTerm pane metadata through its local mux CLI."""
    active_app = ui.active_app()
    if not active_app or active_app.bundle != _WEZTERM_BUNDLE:
        return None

    window = ui.active_window()
    window_title = _scope_text(window.title if window else None)
    if window_title == _NONE:
        # macOS can report an empty title while a newly activated WezTerm
        # window is still being constructed; a later title event will retry.
        return None

    result = {
        "title": window_title,
        "cwd": _NONE,
        "terminal_id": _NONE,
        "window_id": _NONE,
        "window_title": window_title,
        "tab_id": _NONE,
        "tab_name": _NONE,
        "tab_index": _NONE,
        "command": window_title,
    }
    wezterm = _wezterm_path()
    if wezterm is None:
        return result

    cli_result = _run([wezterm, "cli", "list", "--format", "json"])
    if cli_result.returncode != 0:
        return result
    try:
        panes = json.loads(cli_result.stdout)
    except json.JSONDecodeError:
        return result
    if not isinstance(panes, list):
        return result

    selected_tab_index, pane_title = _wezterm_selected_tab(window_title)
    # `wezterm cli list` does not update `window_title` when a tab changes,
    # but the selected pane/tab title is present in the macOS window title.
    # Use it to identify the CLI window before resolving its selected tab.
    matching_window_ids = {
        pane.get("window_id")
        for pane in panes
        if _scope_text(pane.get("title")) == pane_title
        or _scope_text(pane.get("tab_title")) == pane_title
    }
    if len(matching_window_ids) == 1:
        window_id = matching_window_ids.pop()
        window_panes = [pane for pane in panes if pane.get("window_id") == window_id]
    elif len({pane.get("window_id") for pane in panes}) == 1:
        window_panes = panes
    else:
        return result
    tab_ids = []
    for candidate in window_panes:
        tab_id = candidate.get("tab_id")
        if tab_id not in tab_ids:
            tab_ids.append(tab_id)

    # `is_active` means the focused pane *within each tab*, not the selected
    # tab. The macOS title convention starts with `[current/total]`, which
    # unambiguously identifies the selected tab even when its pane title is
    # shared by other tabs.
    if selected_tab_index is not None and 1 <= selected_tab_index <= len(tab_ids):
        selected_tab_id = tab_ids[selected_tab_index - 1]
        candidates = [
            pane for pane in window_panes if pane.get("tab_id") == selected_tab_id
        ]
    else:
        candidates = window_panes
    title_matches = [
        pane
        for pane in candidates
        if _scope_text(pane.get("title")) == pane_title
        or _scope_text(pane.get("tab_title")) == pane_title
    ]
    active_matches = [pane for pane in candidates if pane.get("is_active") is True]
    if len(title_matches) == 1:
        pane = title_matches[0]
    elif len(active_matches) == 1:
        pane = active_matches[0]
    elif len(candidates) == 1:
        pane = candidates[0]
    else:
        return result
    cwd = _scope_text(pane.get("cwd"))
    if cwd.startswith("file://"):
        cwd = _scope_text(unquote(urlparse(cwd).path))

    result.update(
        {
            "title": _scope_text(pane.get("title")),
            "cwd": cwd,
            "terminal_id": _scope_text(pane.get("pane_id")),
            "window_id": _scope_text(pane.get("window_id")),
            "window_title": _scope_text(pane.get("window_title")),
            "tab_id": _scope_text(pane.get("tab_id")),
            "tab_name": _scope_text(pane.get("tab_title") or pane.get("title")),
            "tab_index": _scope_text(tab_ids.index(pane.get("tab_id")) + 1),
            "command": _wezterm_foreground_command(
                _scope_text(pane.get("tty_name"))
            ),
        }
    )
    return result


def _wezterm_selected_tab(window_title: str) -> tuple[int | None, str]:
    """Extract WezTerm's one-based macOS selected-tab prefix, when present."""
    match = re.match(r"^\[(\d+)/(\d+)\]\s+(.+)$", window_title)
    if match is None:
        return None, window_title
    return int(match.group(1)), match.group(3)


def _wezterm_foreground_command(tty_name: str) -> str:
    """Return the foreground process command for a WezTerm pseudo-terminal."""
    if tty_name in (_NONE, _UNKNOWN):
        return _NONE
    result = _run(
        [
            "/bin/ps",
            "-t",
            tty_name.removeprefix("/dev/"),
            "-o",
            "stat=",
            "-o",
            "command=",
        ]
    )
    if result.returncode != 0:
        return _NONE
    for line in result.stdout.splitlines():
        state, _, command = line.strip().partition(" ")
        if "+" in state and command:
            return command.strip()
    return _NONE


def _active_terminal() -> dict[str, str] | None:
    """Return metadata for the active supported terminal application."""
    active_app = ui.active_app()
    if not active_app:
        return None
    if active_app.bundle == _GHOSTTY_BUNDLE:
        return _ghostty_terminal()
    if active_app.bundle == _WEZTERM_BUNDLE:
        return _wezterm_terminal()
    return None


def _zellij_sessions(zellij: str) -> list[str]:
    result = _run([zellij, "list-sessions", "--short"])
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _zellij_session_for_title(title: str, sessions: list[str]) -> str | None:
    """Match a terminal's '<session> | <pane title>' Zellij title convention."""
    matches = [
        session
        for session in sessions
        if title == session or title.startswith(f"{session} | ")
    ]
    if matches:
        return max(matches, key=len)
    return None


def _program_name(command_or_title: Any) -> str:
    """Reduce a command/title to an executable-like value for scope matching."""
    value = str(command_or_title or "").strip()
    if not value:
        return _UNKNOWN

    try:
        parts = shlex.split(value)
    except ValueError:
        parts = value.split()
    if not parts:
        return _UNKNOWN

    program = os.path.basename(parts[0])
    # GUI terminal launchers commonly invoke a command through a shell. For
    # example, Pi's wrapper appears as `/bin/bash .../pi`; expose the actual
    # script so program-scoped Talon contexts continue to identify Pi.
    if program in {"bash", "zsh", "sh", "dash", "ksh"} and len(parts) > 1:
        script = os.path.basename(parts[1])
        if script and not script.startswith("-"):
            return script
    return program or _UNKNOWN


def _zellij_state(
    zellij: str, session: str, terminal_title: str
) -> dict[str, Any] | None:
    """Find the focused pane and its tab metadata for a Ghostty surface."""
    list_result = _run([zellij, "--session", session, "action", "list-panes", "--json"])
    if list_result.returncode != 0:
        return None

    try:
        panes = json.loads(list_result.stdout)
    except json.JSONDecodeError:
        return None
    if not isinstance(panes, list):
        return None

    terminal_panes = [pane for pane in panes if not pane.get("is_plugin", False)]
    focused_panes = [pane for pane in terminal_panes if pane.get("is_focused") is True]

    prefix = f"{session} | "
    pane_title = (
        terminal_title[len(prefix) :] if terminal_title.startswith(prefix) else ""
    )
    selected_pane = None
    selected_by_title = False

    # is_focused is retained for each tab, so the Ghostty title is the best way
    # to identify the selected pane when a session has multiple tabs/clients.
    if pane_title:
        title_matches = [
            pane
            for pane in focused_panes
            if str(pane.get("title", "")).strip() == pane_title
        ]
        if len(title_matches) == 1:
            selected_pane = title_matches[0]
            selected_by_title = True

    tab_info: dict[str, Any] = {}
    tab_result = _run(
        [zellij, "--session", session, "action", "current-tab-info", "--json"]
    )
    if tab_result.returncode == 0:
        try:
            parsed_tab = json.loads(tab_result.stdout)
            if isinstance(parsed_tab, dict):
                tab_info = parsed_tab
        except json.JSONDecodeError:
            pass

    # Fall back to the active tab when the title format is customized.
    if selected_pane is None and tab_info:
        tab_id = tab_info.get("tab_id")
        tab_panes = [pane for pane in focused_panes if pane.get("tab_id") == tab_id]
        if len(tab_panes) == 1:
            selected_pane = tab_panes[0]

    if selected_pane is None and len(focused_panes) == 1:
        selected_pane = focused_panes[0]

    if selected_pane is None:
        return None

    # Do not apply tab state from another client/tab to the selected pane.
    if tab_info.get("tab_id") != selected_pane.get("tab_id"):
        tab_info = {}

    # current-tab-info is client-specific. When the Ghostty title identified a
    # different client/tab, list-tabs still provides the matching tab's metadata.
    if not tab_info:
        tabs_result = _run(
            [zellij, "--session", session, "action", "list-tabs", "--json"]
        )
        if tabs_result.returncode == 0:
            try:
                tabs = json.loads(tabs_result.stdout)
            except json.JSONDecodeError:
                tabs = []
            if isinstance(tabs, list):
                matching_tabs = [
                    tab
                    for tab in tabs
                    if tab.get("tab_id") == selected_pane.get("tab_id")
                ]
                if len(matching_tabs) == 1:
                    tab_info = matching_tabs[0]

    # The title match came from the selected Ghostty surface, so it is the
    # active tab for our purposes even if Zellij reports another client's tab
    # as globally active.
    if selected_by_title:
        tab_info = dict(tab_info)
        tab_info["tab_id"] = selected_pane.get("tab_id")
        tab_info["active"] = True

    return {"pane": selected_pane, "tab": tab_info}


def _zellij_scope_values(session: str, state: dict[str, Any]) -> dict[str, str]:
    pane = state["pane"]
    tab = state.get("tab", {})
    command = pane.get("pane_command")
    title = pane.get("title")

    values = {
        "zellij_session": session,
        "zellij_program": _program_name(command or title),
        "zellij_command": _scope_text(command),
        "zellij_title": _scope_text(title),
        "zellij_cwd": _scope_text(pane.get("pane_cwd")),
        "zellij_pane_id": _scope_text(
            f"{'plugin' if pane.get('is_plugin') else 'terminal'}_{pane.get('id')}"
        ),
        "zellij_pane_numeric_id": _scope_text(pane.get("id")),
        "zellij_pane_type": "plugin" if pane.get("is_plugin") else "terminal",
        "zellij_tab_id": _scope_text(
            _first_present(pane.get("tab_id"), tab.get("tab_id"))
        ),
        "zellij_tab_name": _scope_text(
            _first_present(pane.get("tab_name"), tab.get("name"))
        ),
    }

    for source, target in _PANE_SCOPE_FIELDS.items():
        values[target] = _scope_text(pane.get(source))

    for source, target in _TAB_SCOPE_FIELDS.items():
        values[target] = _scope_text(tab.get(source))

    # These are present in pane JSON and are useful even when current-tab-info
    # cannot identify tab state for a multi-client session.
    values["zellij_tab_position"] = _scope_text(
        _first_present(pane.get("tab_position"), tab.get("position"))
    )
    values["zellij_tab_name"] = _scope_text(
        _first_present(pane.get("tab_name"), tab.get("name"))
    )
    values["zellij_tab_id"] = _scope_text(
        _first_present(pane.get("tab_id"), tab.get("tab_id"))
    )

    return values


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
    zellij = _zellij_path()
    if zellij is None:
        scope["terminal_program"] = native_program
        scope["terminal_focused_program"] = native_program
        scope["terminal_command"] = native_command
        scope["terminal_is_zellij"] = "false"
        return scope

    sessions = _zellij_sessions(zellij)
    session = _zellij_session_for_title(terminal["title"], sessions)
    if (
        session is None
        and _program_name(terminal["title"]).lower() == "zellij"
        and len(sessions) == 1
    ):
        session = sessions[0]

    if session is None:
        scope["terminal_program"] = native_program
        scope["terminal_focused_program"] = native_program
        scope["terminal_command"] = native_command
        scope["terminal_is_zellij"] = "false"
        return scope

    scope["terminal_program"] = "zellij"
    scope["terminal_command"] = "zellij"
    scope["terminal_is_zellij"] = "true"

    state = _zellij_state(zellij, session, terminal["title"])
    scope["zellij_session"] = session
    if state is not None:
        scope.update(_zellij_scope_values(session, state))
    else:
        scope["zellij_program"] = _UNKNOWN
    scope["terminal_focused_program"] = scope["zellij_program"]
    return scope


@mod.scope
def samwho_terminal_scope() -> dict[str, str]:
    """Expose terminal and nested Zellij metadata as user.* scope values."""
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
        f"user.zellij_program = {new_scope['zellij_program']}"
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
            new_scope["terminal_is_zellij"] = _UNKNOWN

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
# terminals update their visible title as focus changes, so these events cover
# native and Zellij navigation without a standing timer.
ui.register("app_activate", _schedule_poll)
ui.register("app_deactivate", _schedule_poll)
ui.register("win_focus", _schedule_poll)
ui.register("win_title", _schedule_poll)


@mod.action_class
class GhosttyActions:
    def samwho_ghostty_action(action: str) -> None:
        """Perform a Ghostty action on the focused terminal surface."""
        _perform_ghostty_action(action)

    def samwho_ghostty_goto_tab(number: int) -> None:
        """Select a Ghostty tab by its one-based index."""
        if number < 1:
            raise ValueError("Ghostty tab numbers start at one")
        _perform_ghostty_action(f"goto_tab:{number}")


# Ghostty 1.3+ exposes its keybind actions through AppleScript. Calling the
# action directly is more reliable than synthesizing a shortcut: it continues
# to work when the user changes Ghostty's keybind configuration, and it lets
# voice commands reach actions that do not have a default shortcut.
def _focused_ghostty_terminal() -> tuple[Any, Any]:
    active_app = ui.active_app()
    if not active_app or active_app.bundle != _GHOSTTY_BUNDLE:
        raise RuntimeError("Ghostty is not the active application")

    ghostty = active_app.appscript()
    if not ghostty.frontmost():
        raise RuntimeError("Ghostty is not frontmost")

    window = ghostty.front_window()
    tab = window.selected_tab()
    return ghostty, tab.focused_terminal()


def _perform_ghostty_action(action: str) -> None:
    if not action:
        raise ValueError("Ghostty action must not be empty")

    try:
        ghostty, terminal = _focused_ghostty_terminal()
        # Ghostty returns false for valid actions that are currently a no-op,
        # such as selecting the already-selected tab. Only an AppleScript
        # exception means that the action could not be dispatched.
        ghostty.perform_action(action, on=terminal)
    except Exception as error:
        raise RuntimeError(f"Ghostty action {action!r} failed: {error}") from error


# Implement Community's shared tab contract for Ghostty.
# Zellij has a more-specific context in zellij.py, so its own tab bindings win.
ghostty_ctx = Context()
ghostty_ctx.matches = """
app: samwho_ghostty
"""


@ghostty_ctx.action_class("app")
class GhosttyAppActions:
    def tab_open():
        _perform_ghostty_action("new_tab")

    def tab_previous():
        _perform_ghostty_action("previous_tab")

    def tab_next():
        _perform_ghostty_action("next_tab")

    def tab_close():
        # cmd-w closes only the focused surface in Ghostty. The Community
        # app.tab_close contract means close the whole current tab.
        _perform_ghostty_action("close_tab:this")

    def tab_reopen():
        # Ghostty's default cmd-shift-t is its undo action; closing a tab is
        # one of the undoable operations.
        _perform_ghostty_action("undo")

    def window_open():
        _perform_ghostty_action("new_window")

    def window_close():
        _perform_ghostty_action("close_window")

    def window_previous():
        _perform_ghostty_action("goto_window:previous")

    def window_next():
        _perform_ghostty_action("goto_window:next")


@ghostty_ctx.action_class("user")
class GhosttySplitActions:
    """Implement Community's shared split vocabulary for Ghostty."""

    # Ghostty's directional split actions create a new split. This is the
    # closest native equivalent to the shared split contract's directional
    # operations.
    def split_window_right():
        _perform_ghostty_action("new_split:right")

    def split_window_left():
        _perform_ghostty_action("new_split:left")

    def split_window_down():
        _perform_ghostty_action("new_split:down")

    def split_window_up():
        _perform_ghostty_action("new_split:up")

    def split_window_vertically():
        _perform_ghostty_action("new_split:right")

    def split_window_horizontally():
        _perform_ghostty_action("new_split:down")

    def split_maximize():
        _perform_ghostty_action("toggle_split_zoom")

    def split_reset():
        _perform_ghostty_action("equalize_splits")

    def split_window():
        _perform_ghostty_action("new_split:right")

    def split_clear():
        _perform_ghostty_action("close_surface")

    def split_next():
        _perform_ghostty_action("goto_split:next")

    def split_last():
        _perform_ghostty_action("goto_split:previous")

    def split_flip():
        raise RuntimeError("Ghostty does not support flipping split orientation")

    def split_clear_all():
        raise RuntimeError("Ghostty does not support clearing all splits")

    def split_number(index: int):
        raise RuntimeError(f"Ghostty does not support selecting split number {index}")


@ghostty_ctx.action_class("user")
class GhosttyCommandSearchActions:
    def command_search(command: str = ""):
        _perform_ghostty_action("toggle_command_palette")
        if command:
            actions.insert(command)


native_ghostty_ctx = Context()
native_ghostty_ctx.matches = """
app: samwho_ghostty
user.terminal_is_zellij: false
"""


@native_ghostty_ctx.action_class("user")
class NativeGhosttyUserActions:
    def tab_jump(number: int):
        if number < 1:
            raise ValueError("Ghostty tab numbers start at one")
        _perform_ghostty_action(f"goto_tab:{number}")

    def tab_final():
        _perform_ghostty_action("last_tab")

    def tab_duplicate():
        raise RuntimeError("Ghostty has no native duplicate-tab action")


@ghostty_ctx.action_class("user")
class GhosttyFileManagerActions:
    def file_manager_current_path() -> str:
        with _state_lock:
            if _current_scope["terminal_is_zellij"] == "true":
                path = _current_scope["zellij_cwd"]
                if path in (_NONE, _UNKNOWN):
                    path = _current_scope["terminal_cwd"]
            else:
                path = _current_scope["terminal_cwd"]

        if path in (_NONE, _UNKNOWN):
            raise RuntimeError("Ghostty did not report the current directory")
        return path


cron.after("0ms", _start_poll)
