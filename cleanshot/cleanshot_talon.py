from talon import Context, Module, actions, ui

from .cleanshot_client import CaptureAction, Cleanshot, is_installed

mod = Module()
mod.tag(
    "samwho_cleanshot_installed",
    desc="Active when CleanShot X is installed on this Mac",
)


ctx_availability = Context()
if is_installed():
    ctx_availability.tags = ["user.samwho_cleanshot_installed"]

ctx_mac = Context()
ctx_mac.matches = """
os: mac
tag: user.samwho_cleanshot_installed
"""


def _capture_rect(rect: ui.Rect, action: CaptureAction) -> None:
    """Capture a Talon rectangle using CleanShot's display-local coordinates."""
    screens = ui.screens()

    def overlap_area(screen: ui.Screen) -> float:
        screen_rect = screen.rect
        width = max(
            0,
            min(rect.x + rect.width, screen_rect.x + screen_rect.width)
            - max(rect.x, screen_rect.x),
        )
        height = max(
            0,
            min(rect.y + rect.height, screen_rect.y + screen_rect.height)
            - max(rect.y, screen_rect.y),
        )
        return width * height

    selected_screen = max(screens, key=overlap_area)
    screen_rect = selected_screen.rect
    Cleanshot.capture_area(
        x=round(rect.x - screen_rect.x),
        y=round(screen_rect.height - (rect.y - screen_rect.y) - rect.height),
        width=round(rect.width),
        height=round(rect.height),
        display=screens.index(selected_screen) + 1,
        action=action,
    )


@ctx_mac.action_class("user")
class ScreenshotActions:
    def screenshot(screen_number: int | None = None):
        if screen_number is None:
            Cleanshot.capture_fullscreen(action="save")
            return

        selected_screen = actions.user.screens_get_by_number(screen_number)
        _capture_rect(selected_screen.rect, "save")

    def screenshot_window():
        _capture_rect(ui.active_window().rect, "save")

    def screenshot_selection():
        Cleanshot.capture_area(action="save")

    def screenshot_selection_clip():
        Cleanshot.capture_area(action="copy")

    def screenshot_settings():
        Cleanshot.open_settings("screenshots")

    def screenshot_clipboard(screen_number: int | None = None):
        if screen_number is None:
            Cleanshot.capture_fullscreen(action="copy")
            return

        selected_screen = actions.user.screens_get_by_number(screen_number)
        _capture_rect(selected_screen.rect, "copy")

    def screenshot_window_clipboard():
        _capture_rect(ui.active_window().rect, "copy")

    def screenshot_rect(rect: ui.Rect, title: str = ""):
        _capture_rect(rect, "save")


@mod.action_class
class Actions:
    def samwho_cleanshot_annotate() -> None:
        """Open the clipboard image in CleanShot's annotator."""
        Cleanshot.open_from_clipboard()

    def samwho_cleanshot_capture_history() -> None:
        """Open CleanShot's capture history."""
        Cleanshot.open_capture_history()
