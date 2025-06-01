import os

from talon import Module, actions, app
from talon.plugins import eye_zoom_mouse

eye_zoom_mouse.config.eye_avg = 7

mod = Module()


def on_ready():
    actions.user.wake()

    global default_mic
    default_mic = actions.sound.active_microphone()

    print(f"Default mic: {default_mic}")


app.register("ready", on_ready)


@mod.action_class
class Actions:
    def open_obsidian_daily_note():
        """My custom date function"""
        return os.system(
            'open "obsidian://advanced-uri?vault=Universe&daily=true&mode=append"'
        )

    def correct(phrase: list[str]):
        """Correct a word"""
        idx = actions.user.find_phrase(phrase)
        if idx is None:
            return

        actions.edit.select_all()
        actions.key("left")
        for _ in range(idx):
            actions.key("right")

        for _ in range(len(" ".join(phrase))):
            actions.edit.extend_right()

        return idx

    def selectXY(start: list[str], end: list[str]):
        """Select from start to end"""
        start_idx = actions.user.find_phrase(start)
        if start_idx is None:
            return

        end_idx = actions.user.find_phrase(end)
        if end_idx is None:
            return

        end_idx += len(" ".join(end))

        actions.edit.select_all()
        actions.key("left")
        for _ in range(start_idx):
            actions.key("right")

        for _ in range(end_idx - start_idx):
            actions.edit.extend_right()

    def find_phrase(phrase: list[str]) -> int | None:
        """Find a word"""
        actions.edit.select_all()
        text = actions.edit.selected_text()
        actions.edit.select_none()

        idx = text.lower().find(" ".join(phrase).lower())
        if idx == -1:
            return None
        return idx

    def wake():
        """Wake Talon"""
        actions.tracking.control_zoom_toggle(True)
        actions.speech.enable()

    def sleep():
        """Sleep Talon"""
        actions.tracking.control_zoom_toggle(False)
        actions.speech.disable()

    def wake_toggle():
        """Toggle Talon wake/sleep"""
        if actions.speech.enabled():
            actions.user.sleep()
        else:
            actions.user.wake()

    def track():
        """Toggle mouse tracking"""
        if actions.tracking.control_enabled():
            actions.user.track_off()
        else:
            actions.user.track_on()

    def screenshot_start():
        """Start a screenshot"""
        actions.key("f13")
        actions.sleep(0.1)
        actions.user.mouse_drag(0)
        actions.user.track_on()

    def screenshot_end():
        """End a screenshot"""
        actions.user.mouse_drag_end()
        actions.user.track_off()

    def track_on():
        """Turn on mouse tracking"""
        if actions.tracking.control_enabled():
            return
        actions.tracking.control_toggle(True)
        actions.tracking.control_zoom_toggle(False)
        actions.tracking.control_gaze_toggle(True)
        actions.tracking.control_head_toggle(True)

    def track_off():
        """Turn off mouse tracking"""
        if not actions.tracking.control_enabled():
            return
        actions.tracking.control_toggle(False)
        actions.tracking.control_zoom_toggle(True)
        actions.tracking.control_gaze_toggle(False)
        actions.tracking.control_head_toggle(False)

    def mute_mic():
        """Mute microphone"""
        actions.sound.set_microphone("None")

    def unmute_mic():
        """Unmute microphone"""
        actions.sound.set_microphone(default_mic)

    def talon_restart():
        """Restart talon"""
        os.system("restart-talon")
