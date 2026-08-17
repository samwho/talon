from typing import Any

from talon import Context, Module, actions, ui

mod = Module()
mod.apps.samwho_ghostty = """
os: mac
and app.bundle: com.mitchellh.ghostty
"""

_GHOSTTY_BUNDLE = "com.mitchellh.ghostty"


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
