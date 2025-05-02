from talon import Context, actions

ctx_mac = Context()
ctx_mac.matches = r"""
os: mac
"""


@ctx_mac.action_class("user")
class UserActionsMac:
    def screenshot_selection():
        actions.key("f13")

    def screenshot_selection_clip():
        actions.key("f13")
