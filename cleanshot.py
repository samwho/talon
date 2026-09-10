import subprocess
from pathlib import Path
from typing import Literal
from urllib.parse import quote, urlencode

from talon import Context, Module, actions, ui

mod = Module()
mod.tag(
    "samwho_cleanshot_installed",
    desc="Active when CleanShot X is installed on this Mac",
)


def _is_cleanshot_installed() -> bool:
    common_locations = (
        Path("/Applications/CleanShot X.app"),
        Path.home() / "Applications/CleanShot X.app",
    )
    if any(path.exists() for path in common_locations):
        return True

    try:
        result = subprocess.run(
            [
                "/usr/bin/mdfind",
                "kMDItemCFBundleIdentifier == 'pl.maketheweb.cleanshotx'",
            ],
            capture_output=True,
            text=True,
            timeout=1,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False

    return result.returncode == 0 and bool(result.stdout.strip())


ctx_availability = Context()
if _is_cleanshot_installed():
    ctx_availability.tags = ["user.samwho_cleanshot_installed"]

ctx_mac = Context()
ctx_mac.matches = """
os: mac
tag: user.samwho_cleanshot_installed
"""

CaptureAction = Literal["copy", "save", "annotate", "upload", "pin"]
SettingsTab = Literal[
    "general",
    "wallpaper",
    "shortcuts",
    "quickaccess",
    "recording",
    "screenshots",
    "annotate",
    "cloud",
    "advanced",
    "about",
]


class Cleanshot:
    """Python interface to CleanShot X's URL scheme API."""

    @staticmethod
    def _open(command: str, **parameters: object) -> None:
        query_parameters = {
            name: str(value).lower() if isinstance(value, bool) else str(value)
            for name, value in parameters.items()
            if value is not None
        }
        query = urlencode(query_parameters, quote_via=quote, safe="/")
        url = f"cleanshot://{command}"
        if query:
            url = f"{url}?{query}"

        subprocess.Popen(
            ["/usr/bin/open", url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    @staticmethod
    def all_in_one(
        *,
        x: int | None = None,
        y: int | None = None,
        width: int | None = None,
        height: int | None = None,
        display: int | None = None,
    ) -> None:
        """Launch All-In-One mode, optionally at a specific screen region."""
        Cleanshot._open(
            "all-in-one",
            x=x,
            y=y,
            width=width,
            height=height,
            display=display,
        )

    @staticmethod
    def capture_area(
        *,
        x: int | None = None,
        y: int | None = None,
        width: int | None = None,
        height: int | None = None,
        display: int | None = None,
        action: CaptureAction | None = None,
    ) -> None:
        """Open area capture, or instantly capture a supplied screen region."""
        Cleanshot._open(
            "capture-area",
            x=x,
            y=y,
            width=width,
            height=height,
            display=display,
            action=action,
        )

    @staticmethod
    def capture_previous_area(*, action: CaptureAction | None = None) -> None:
        """Repeat the most recent area capture."""
        Cleanshot._open("capture-previous-area", action=action)

    @staticmethod
    def capture_fullscreen(*, action: CaptureAction | None = None) -> None:
        """Capture the full screen."""
        Cleanshot._open("capture-fullscreen", action=action)

    @staticmethod
    def capture_window(*, action: CaptureAction | None = None) -> None:
        """Open window capture mode."""
        Cleanshot._open("capture-window", action=action)

    @staticmethod
    def self_timer(*, action: CaptureAction | None = None) -> None:
        """Open area capture mode with the self-timer."""
        Cleanshot._open("self-timer", action=action)

    @staticmethod
    def scrolling_capture(
        *,
        x: int | None = None,
        y: int | None = None,
        width: int | None = None,
        height: int | None = None,
        display: int | None = None,
        start: bool | None = None,
        autoscroll: bool | None = None,
    ) -> None:
        """Open scrolling capture, optionally configured for a screen region."""
        Cleanshot._open(
            "scrolling-capture",
            x=x,
            y=y,
            width=width,
            height=height,
            display=display,
            start=start,
            autoscroll=autoscroll,
        )

    @staticmethod
    def pin(filepath: str | Path | None = None) -> None:
        """Pin an image, or show CleanShot's file picker when no path is given."""
        Cleanshot._open("pin", filepath=filepath)

    @staticmethod
    def record_screen(
        *,
        x: int | None = None,
        y: int | None = None,
        width: int | None = None,
        height: int | None = None,
        display: int | None = None,
    ) -> None:
        """Open screen recording mode, optionally at a specific screen region."""
        Cleanshot._open(
            "record-screen",
            x=x,
            y=y,
            width=width,
            height=height,
            display=display,
        )

    @staticmethod
    def capture_text(
        filepath: str | Path | None = None,
        *,
        x: int | None = None,
        y: int | None = None,
        width: int | None = None,
        height: int | None = None,
        display: int | None = None,
        linebreaks: bool | None = None,
    ) -> None:
        """OCR a file or a selected/supplied screen region."""
        Cleanshot._open(
            "capture-text",
            filepath=filepath,
            x=x,
            y=y,
            width=width,
            height=height,
            display=display,
            linebreaks=linebreaks,
        )

    @staticmethod
    def open_annotate(filepath: str | Path | None = None) -> None:
        """Annotate an image, or show CleanShot's file picker without a path."""
        Cleanshot._open("open-annotate", filepath=filepath)

    @staticmethod
    def open_from_clipboard() -> None:
        """Open the clipboard image in Annotate."""
        Cleanshot._open("open-from-clipboard")

    @staticmethod
    def toggle_desktop_icons() -> None:
        """Toggle Desktop icon visibility."""
        Cleanshot._open("toggle-desktop-icons")

    @staticmethod
    def hide_desktop_icons() -> None:
        """Hide Desktop icons."""
        Cleanshot._open("hide-desktop-icons")

    @staticmethod
    def show_desktop_icons() -> None:
        """Show Desktop icons."""
        Cleanshot._open("show-desktop-icons")

    @staticmethod
    def add_quick_access_overlay(filepath: str | Path) -> None:
        """Add an image or video to the Quick Access Overlay."""
        Cleanshot._open("add-quick-access-overlay", filepath=filepath)

    @staticmethod
    def open_capture_history() -> None:
        """Open capture history."""
        Cleanshot._open("open-history")

    @staticmethod
    def restore_recently_closed() -> None:
        """Restore the most recently closed file from capture history."""
        Cleanshot._open("restore-recently-closed")

    @staticmethod
    def open_settings(tab: SettingsTab | None = None) -> None:
        """Open CleanShot settings, optionally on a specific tab."""
        Cleanshot._open("open-settings", tab=tab)


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
