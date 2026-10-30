import json

from talon import Context, Module, actions, settings, ui

from .rex_attention import focus_next_waiting
from .rex_client import REX_BUNDLE, Rex

mod = Module()
mod.apps.samwho_rex = f"""
os: mac
and app.bundle: {REX_BUNDLE}
"""
mod.setting(
    "samwho_rex_client",
    type=str,
    default="",
    desc="Rex client label or ID; empty lets Rex select the sole connected app",
)


@mod.action_class
class RexActions:
    def samwho_rex_action(action: str, arguments: str = "{}") -> None:
        """Perform a named Rex action with optional JSON object arguments."""
        parameters = json.loads(arguments)
        if not isinstance(parameters, dict):
            raise ValueError("Rex action arguments must be a JSON object")
        _perform_action(action, parameters)

    def samwho_rex_waiting_next() -> None:
        """Focus the next done or blocked terminal in the current Rex session."""
        active_app = ui.active_app()
        if active_app is None or active_app.bundle != REX_BUNDLE:
            raise RuntimeError("Rex is not the active application")
        focus_next_waiting(
            Rex(client=settings.get("user.samwho_rex_client")), active_app.pid
        )


def _perform_action(action: str, arguments: dict | None = None) -> None:
    Rex(client=settings.get("user.samwho_rex_client")).perform_action(action, arguments)


ctx = Context()
ctx.matches = """
app: samwho_rex
"""


@ctx.action_class("edit")
class RexFindActions:
    def find(text=None):
        _perform_action("client.find.open")
        if text:
            actions.insert(text)

    def find_next():
        _perform_action("client.find.next")

    def find_previous():
        _perform_action("client.find.previous")


@ctx.action_class("user")
class RexCommandSearchActions:
    def command_search(command: str = ""):
        _perform_action("client.palette.toggle")
        if command:
            actions.insert(command)


@ctx.action_class("app")
class RexTabActions:
    """Implement Community's tab actions without synthesized shortcuts."""

    def tab_open():
        _perform_action("client.tab.new")

    def tab_previous():
        _perform_action("client.tab.previous")

    def tab_next():
        _perform_action("client.tab.next")

    def tab_close():
        _perform_action("client.tab.close")

    def tab_reopen():
        raise RuntimeError("Rex does not expose a reopen-tab action")


@ctx.action_class("user")
class RexCommunityActions:
    """Implement Community's shared tab and split contracts for Rex."""

    def tab_jump(number: int):
        if number < 1:
            raise ValueError("Rex tab numbers start at one")
        _perform_action("client.tab.goto", {"index": number})

    def tab_final():
        _perform_action("client.tab.goto", {"index": -1})

    def tab_duplicate():
        raise RuntimeError("Rex does not expose a duplicate-tab action")

    # Like Ghostty and Herdr, directional splits create a new terminal rather
    # than moving an editor document into another split.
    def split_window_right():
        _perform_action("pane.split.right")

    def split_window_left():
        _perform_action("pane.split.left")

    def split_window_down():
        _perform_action("pane.split.down")

    def split_window_up():
        _perform_action("pane.split.up")

    def split_window_vertically():
        _perform_action("pane.split.right")

    def split_window_horizontally():
        _perform_action("pane.split.down")

    def split_window():
        _perform_action("pane.split.auto")

    def split_maximize():
        _perform_action("pane.zoom")

    def split_reset():
        _perform_action("pane.balance")

    def split_clear():
        _perform_action("pane.close")

    def split_next():
        _perform_action("pane.focus_next")

    def split_last():
        _perform_action("pane.focus_previous")

    def split_flip():
        raise RuntimeError("Rex does not expose a flip-split action")

    def split_clear_all():
        raise RuntimeError("Rex does not expose an action to clear all splits")

    def split_number(index: int):
        raise RuntimeError(
            f"Rex does not expose an action to focus split number {index}"
        )
