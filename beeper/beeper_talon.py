from talon import Context, Module, actions

mod = Module()
mod.apps.samwho_beeper = """
os: mac
and app.bundle: com.automattic.beeper.desktop
"""

ctx = Context()
ctx.matches = "app: samwho_beeper"


@ctx.action_class("user")
class UserActions:
    def messaging_workspace_previous():
        raise RuntimeError("Beeper workspace navigation is not configured")

    def messaging_workspace_next():
        raise RuntimeError("Beeper workspace navigation is not configured")

    def messaging_channel_previous():
        raise RuntimeError("Beeper channel navigation is not configured")

    def messaging_channel_next():
        raise RuntimeError("Beeper channel navigation is not configured")

    def messaging_unread_previous():
        raise RuntimeError("Beeper previous-unread navigation is not configured")

    def messaging_unread_next():
        actions.key("cmd-u")

    def messaging_mark_workspace_read():
        raise RuntimeError("Beeper workspace read-state control is not configured")

    def messaging_mark_channel_read():
        raise RuntimeError("Beeper channel read-state control is not configured")

    def messaging_upload_file():
        raise RuntimeError("Beeper file upload is not configured")

    def messaging_open_search():
        actions.key("cmd-k")
