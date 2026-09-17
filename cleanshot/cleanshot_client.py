import subprocess
from pathlib import Path
from typing import Literal
from urllib.parse import quote, urlencode


def is_installed() -> bool:
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


