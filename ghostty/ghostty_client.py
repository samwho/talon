from dataclasses import dataclass
from typing import Any

from talon import ui

GHOSTTY_BUNDLE = "com.mitchellh.ghostty"


class GhosttyError(RuntimeError):
    """Raised when Ghostty cannot provide or act on its focused terminal."""


@dataclass(frozen=True)
class GhosttyTerminalSnapshot:
    title: Any
    cwd: Any
    terminal_id: Any
    window_id: Any
    window_title: Any
    tab_id: Any
    tab_name: Any
    tab_index: Any


def _focused_surface() -> tuple[Any, Any, Any, Any]:
    active_app = ui.active_app()
    if not active_app or active_app.bundle != GHOSTTY_BUNDLE:
        raise GhosttyError("Ghostty is not the active application")

    try:
        ghostty = active_app.appscript()
        if not ghostty.frontmost():
            raise GhosttyError("Ghostty is not frontmost")
        window = ghostty.front_window()
        tab = window.selected_tab()
        terminal = tab.focused_terminal()
    except GhosttyError:
        raise
    except Exception as error:
        raise GhosttyError(f"Ghostty AppleScript query failed: {error}") from error

    return ghostty, window, tab, terminal


def snapshot() -> GhosttyTerminalSnapshot | None:
    """Return metadata for Ghostty's focused terminal when Ghostty is active."""
    active_app = ui.active_app()
    if not active_app or active_app.bundle != GHOSTTY_BUNDLE:
        return None

    _, window, tab, terminal = _focused_surface()
    return GhosttyTerminalSnapshot(
        title=terminal.name(),
        cwd=terminal.working_directory(),
        terminal_id=terminal.id(),
        window_id=window.id(),
        window_title=window.name(),
        tab_id=tab.id(),
        tab_name=tab.name(),
        tab_index=tab.index(),
    )


def perform_action(action: str) -> None:
    """Perform a Ghostty keybind action on the focused terminal."""
    if not action:
        raise ValueError("Ghostty action must not be empty")

    ghostty, _, _, terminal = _focused_surface()
    try:
        # Ghostty returns false for valid actions that are currently a no-op.
        # Only an AppleScript exception means dispatch failed.
        ghostty.perform_action(action, on=terminal)
    except Exception as error:
        raise GhosttyError(f"Ghostty action {action!r} failed: {error}") from error
