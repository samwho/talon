from talon import Context, actions

ctx = Context()
ctx.matches = r"""
app: samwho_terminal
user.terminal_focused_program: /^pi$/i
"""


@ctx.action_class("edit")
class PiEditActions:
    """Map Community's editing vocabulary to Pi's editor and transcript."""

    def word_left():
        actions.key("alt-left")

    def word_right():
        actions.key("alt-right")

    def line_start():
        actions.key("ctrl-a")

    def line_end():
        actions.key("ctrl-e")

    def undo():
        actions.key("ctrl--")

    def file_start():
        actions.key("home")

    def file_end():
        actions.key("end")

    def page_up():
        actions.key("pageup")

    def page_down():
        actions.key("pagedown")

    def find(text: str = None):
        actions.key("ctrl-shift-f")
        if text:
            actions.insert(text)

    def find_next():
        actions.key("ctrl-g")

    def find_previous():
        actions.key("ctrl-shift-g")
