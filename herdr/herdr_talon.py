from typing import Any

from talon import Context, Module

from .herdr_client import call as _call
from .herdr_client import current_pane as _current_pane
from .herdr_client import result_list as _result_list

mod = Module()
ctx = Context()
ctx.matches = r"""
app: samwho_terminal
user.terminal_is_herdr: true
"""

_DIRECTIONS = {"left", "right", "up", "down"}


def _current_cwd(pane: dict[str, Any]) -> str | None:
    cwd = pane.get("foreground_cwd") or pane.get("cwd")
    return str(cwd) if cwd else None


def _workspaces() -> list[dict[str, Any]]:
    workspaces = _result_list(("workspace", "list"), "workspaces")
    return sorted(workspaces, key=lambda workspace: workspace.get("number", 0))


def _workspace_tabs(workspace_id: str) -> list[dict[str, Any]]:
    tabs = _result_list(("tab", "list", "--workspace", workspace_id), "tabs")
    return sorted(tabs, key=lambda tab: tab.get("number", 0))


def _workspace_panes(workspace_id: str) -> list[dict[str, Any]]:
    return _result_list(("pane", "list", "--workspace", workspace_id), "panes")


def _agents() -> list[dict[str, Any]]:
    return _result_list(("agent", "list"), "agents")


def _focus_relative(items: list[dict[str, Any]], id_key: str, current_id: str, offset: int, command: tuple[str, ...]) -> None:
    if not items:
        raise RuntimeError("Herdr returned no selectable items")
    current_index = next(
        (index for index, item in enumerate(items) if item.get(id_key) == current_id),
        None,
    )
    if current_index is None:
        current_index = -1 if offset > 0 else 0
    target = items[(current_index + offset) % len(items)]
    _call(*command, str(target[id_key]))


def _create_tab_like_current() -> None:
    pane = _current_pane()
    arguments = ["tab", "create", "--workspace", str(pane["workspace_id"])]
    cwd = _current_cwd(pane)
    if cwd:
        arguments.extend(["--cwd", cwd])
    arguments.append("--focus")
    _call(*arguments)


def _split_pane(direction: str) -> None:
    pane = _current_pane()
    arguments = [
        "pane",
        "split",
        "--pane",
        str(pane["pane_id"]),
        "--direction",
        direction,
    ]
    cwd = _current_cwd(pane)
    if cwd:
        arguments.extend(["--cwd", cwd])
    arguments.append("--focus")
    _call(*arguments)


def _check_direction(direction: str) -> str:
    if direction not in _DIRECTIONS:
        raise ValueError(f"Unknown Herdr direction: {direction}")
    return direction


def _focus_spatial_neighbor(directions: tuple[str, ...]) -> None:
    pane = _current_pane()
    pane_id = str(pane["pane_id"])
    for direction in directions:
        try:
            neighbor = _call(
                "pane", "neighbor", "--pane", pane_id, "--direction", direction
            )["result"]["neighbor"]
        except (KeyError, TypeError):
            continue
        if isinstance(neighbor, dict) and neighbor.get("pane_id") != pane_id:
            _call("pane", "focus", "--pane", pane_id, "--direction", direction)
            return
    raise RuntimeError("Herdr found no neighboring pane")


def _focus_next_done_agent() -> None:
    agents = _agents()
    if not agents:
        raise RuntimeError("Herdr has no recognized agents")
    current_index = next(
        (index for index, agent in enumerate(agents) if agent.get("focused")), -1
    )
    for distance in range(1, len(agents) + 1):
        candidate = agents[(current_index + distance) % len(agents)]
        if candidate.get("agent_status") == "done":
            _call("agent", "focus", str(candidate["pane_id"]))
            return
    raise RuntimeError("Herdr has no unread agents")


@mod.action_class
class HerdrActions:
    """Personal voice actions for Herdr's interactive CLI operations."""

    def samwho_herdr_workspace_new() -> None:
        """Create and focus a workspace using the current pane's directory."""
        pane = _current_pane()
        arguments = ["workspace", "create"]
        cwd = _current_cwd(pane)
        if cwd:
            arguments.extend(["--cwd", cwd])
        arguments.append("--focus")
        _call(*arguments)

    def samwho_herdr_workspace_previous() -> None:
        """Focus the previous workspace, wrapping at the beginning."""
        pane = _current_pane()
        _focus_relative(
            _workspaces(),
            "workspace_id",
            str(pane["workspace_id"]),
            -1,
            ("workspace", "focus"),
        )

    def samwho_herdr_workspace_next() -> None:
        """Focus the next workspace, wrapping at the end."""
        pane = _current_pane()
        _focus_relative(
            _workspaces(),
            "workspace_id",
            str(pane["workspace_id"]),
            1,
            ("workspace", "focus"),
        )

    def samwho_herdr_workspace_jump(number: int) -> None:
        """Focus a workspace by its displayed number."""
        target = next(
            (workspace for workspace in _workspaces() if workspace.get("number") == number),
            None,
        )
        if target is None:
            raise RuntimeError(f"Herdr has no workspace {number}")
        _call("workspace", "focus", str(target["workspace_id"]))

    def samwho_herdr_workspace_rename(label: str) -> None:
        """Rename the focused workspace."""
        pane = _current_pane()
        _call("workspace", "rename", str(pane["workspace_id"]), label)

    def samwho_herdr_workspace_close() -> None:
        """Close the focused workspace unless Herdr requires group confirmation."""
        pane = _current_pane()
        _call("workspace", "close", str(pane["workspace_id"]))

    def samwho_herdr_tab_rename(label: str) -> None:
        """Rename the focused tab."""
        pane = _current_pane()
        _call("tab", "rename", str(pane["tab_id"]), label)

    def samwho_herdr_pane_focus(direction: str) -> None:
        """Focus the neighboring pane in a direction."""
        _call("pane", "focus", "--current", "--direction", _check_direction(direction))

    def samwho_herdr_pane_swap(direction: str) -> None:
        """Swap the focused pane with its neighbor in a direction."""
        _call("pane", "swap", "--current", "--direction", _check_direction(direction))

    def samwho_herdr_pane_resize(direction: str, amount: int) -> None:
        """Move the focused pane's boundary in a direction by a percentage."""
        _call(
            "pane",
            "resize",
            "--current",
            "--direction",
            _check_direction(direction),
            "--amount",
            str(amount / 100),
        )

    def samwho_herdr_pane_rename(label: str) -> None:
        """Rename the focused pane."""
        pane = _current_pane()
        _call("pane", "rename", str(pane["pane_id"]), label)

    def samwho_herdr_pane_name_clear() -> None:
        """Clear the focused pane's custom name."""
        pane = _current_pane()
        _call("pane", "rename", str(pane["pane_id"]), "--clear")

    def samwho_herdr_pane_to_tab() -> None:
        """Move the focused pane into a new tab."""
        pane = _current_pane()
        _call("pane", "move", str(pane["pane_id"]), "--new-tab", "--focus")

    def samwho_herdr_pane_to_workspace() -> None:
        """Move the focused pane into a new workspace."""
        pane = _current_pane()
        _call(
            "pane", "move", str(pane["pane_id"]), "--new-workspace", "--focus"
        )

    def samwho_herdr_unread_next() -> None:
        """Focus the next agent whose Herdr status is Done."""
        _focus_next_done_agent()

    def samwho_herdr_agent_previous() -> None:
        """Focus the previous recognized agent."""
        pane = _current_pane()
        _focus_relative(
            _agents(), "pane_id", str(pane["pane_id"]), -1, ("agent", "focus")
        )

    def samwho_herdr_agent_next() -> None:
        """Focus the next recognized agent."""
        pane = _current_pane()
        _focus_relative(
            _agents(), "pane_id", str(pane["pane_id"]), 1, ("agent", "focus")
        )

    def samwho_herdr_agent_jump(number: int) -> None:
        """Focus a recognized agent by its order in Herdr's agent list."""
        agents = _agents()
        if number < 1 or number > len(agents):
            raise RuntimeError(f"Herdr has no agent {number}")
        _call("agent", "focus", str(agents[number - 1]["pane_id"]))

    def samwho_herdr_agent_rename(name: str) -> None:
        """Assign a voice-friendly name to the focused agent."""
        pane = _current_pane()
        _call("agent", "rename", str(pane["pane_id"]), name)

    def samwho_herdr_agent_name_clear() -> None:
        """Clear the focused agent's custom name."""
        pane = _current_pane()
        _call("agent", "rename", str(pane["pane_id"]), "--clear")

    def samwho_herdr_worktree_create(branch: str) -> None:
        """Create and focus a worktree workspace for a new branch."""
        pane = _current_pane()
        arguments = [
            "worktree",
            "create",
            "--workspace",
            str(pane["workspace_id"]),
            "--branch",
            branch,
            "--focus",
        ]
        cwd = _current_cwd(pane)
        if cwd:
            arguments.extend(["--cwd", cwd])
        _call(*arguments, timeout=5)

    def samwho_herdr_worktree_open(path: str) -> None:
        """Open and focus an existing worktree by path."""
        pane = _current_pane()
        _call(
            "worktree",
            "open",
            "--workspace",
            str(pane["workspace_id"]),
            "--path",
            path,
            "--focus",
            timeout=5,
        )

    def samwho_herdr_worktree_remove() -> None:
        """Remove the focused worktree without forcing or bypassing trust checks."""
        pane = _current_pane()
        _call(
            "worktree",
            "remove",
            "--workspace",
            str(pane["workspace_id"]),
            timeout=5,
        )


@ctx.action_class("app")
class HerdrTabActions:
    """Implement Community's shared tab actions through Herdr's CLI."""

    def tab_open():
        _create_tab_like_current()

    def tab_previous():
        pane = _current_pane()
        _focus_relative(
            _workspace_tabs(str(pane["workspace_id"])),
            "tab_id",
            str(pane["tab_id"]),
            -1,
            ("tab", "focus"),
        )

    def tab_next():
        pane = _current_pane()
        _focus_relative(
            _workspace_tabs(str(pane["workspace_id"])),
            "tab_id",
            str(pane["tab_id"]),
            1,
            ("tab", "focus"),
        )

    def tab_close():
        pane = _current_pane()
        _call("tab", "close", str(pane["tab_id"]))

    def tab_reopen():
        raise RuntimeError("Herdr does not support reopening closed tabs")


@ctx.action_class("user")
class HerdrCommunityActions:
    """Implement Community's shared tab and split action contracts."""

    def tab_jump(number: int):
        pane = _current_pane()
        target = next(
            (
                tab
                for tab in _workspace_tabs(str(pane["workspace_id"]))
                if tab.get("number") == number
            ),
            None,
        )
        if target is None:
            raise RuntimeError(f"Herdr workspace has no tab {number}")
        _call("tab", "focus", str(target["tab_id"]))

    def tab_final():
        pane = _current_pane()
        tabs = _workspace_tabs(str(pane["workspace_id"]))
        if not tabs:
            raise RuntimeError("Herdr workspace has no tabs")
        _call("tab", "focus", str(tabs[-1]["tab_id"]))

    def tab_duplicate():
        _create_tab_like_current()

    def split_window_right():
        _split_pane("right")

    def split_window_left():
        _split_pane("right")
        _call("pane", "swap", "--current", "--direction", "left")

    def split_window_down():
        _split_pane("down")

    def split_window_up():
        _split_pane("down")
        _call("pane", "swap", "--current", "--direction", "up")

    def split_window_vertically():
        _split_pane("right")

    def split_window_horizontally():
        _split_pane("down")

    def split_flip():
        raise RuntimeError("Herdr cannot flip a split's orientation")

    def split_maximize():
        _call("pane", "zoom", "--current", "--toggle")

    def split_reset():
        raise RuntimeError("Herdr cannot automatically equalize split sizes")

    def split_window():
        _split_pane("right")

    def split_clear():
        pane = _current_pane()
        _call("pane", "close", str(pane["pane_id"]))

    def split_clear_all():
        pane = _current_pane()
        panes = _workspace_panes(str(pane["workspace_id"]))
        for other in panes:
            if other.get("tab_id") == pane.get("tab_id") and other.get("pane_id") != pane.get("pane_id"):
                _call("pane", "close", str(other["pane_id"]))

    def split_next():
        _focus_spatial_neighbor(("right", "down", "left", "up"))

    def split_last():
        _focus_spatial_neighbor(("left", "up", "right", "down"))

    def split_number(index: int):
        raise RuntimeError(f"Herdr cannot directly focus split number {index}")
