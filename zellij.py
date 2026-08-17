from talon import Context, actions

ctx = Context()
ctx.matches = """
app: samwho_terminal
user.terminal_is_zellij: true
"""


@ctx.action_class("app")
class ZellijAppActions:
    """Map the shared tab actions to this user's Zellij keybindings."""

    def tab_open():
        actions.key("ctrl-t")

    def tab_previous():
        actions.key("ctrl-h")

    def tab_next():
        actions.key("ctrl-l")

    def tab_close():
        actions.key("alt-w")

    def tab_reopen():
        """Zellij has no native reopen-tab action."""
        raise RuntimeError("Zellij does not support reopening closed tabs")
