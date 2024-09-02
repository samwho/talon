from talon import Context, actions

ctx = Context()
ctx.matches = r"""
os: mac
app: beeper
"""


@ctx.action_class("user")
class UserActions:
    def messaging_workspace_previous():
        pass

    def messaging_workspace_next():
        pass

    def messaging_channel_previous():
        pass

    def messaging_channel_next():
        pass

    def messaging_unread_previous():
        pass

    def messaging_unread_next():
        actions.key("cmd-u")

    def messaging_mark_workspace_read():
        pass

    def messaging_mark_channel_read():
        pass

    def messaging_upload_file():
        pass

    def messaging_open_search():
        actions.key("cmd-k")
