import os

from talon import Module, actions, app, noise
from talon.plugins import eye_zoom_mouse

eye_zoom_mouse.config.eye_avg = 7

mod = Module()
_hiss_scroll_up = False


def _samwho_on_ready():
    actions.user.samwho_wake()


mod.mode("samwho_whisper", desc="For dictation outside of Talon")
mod.mode("samwho_voicenote", desc="For recording voicenotes")

app.register("ready", _samwho_on_ready)


@mod.action_class
class Actions:
    def samwho_noop():
        """Do nothing."""
        actions.sleep(0)

    def samwho_correct(phrase: list[str]):
        """Correct a word"""
        idx = actions.user.samwho_find_phrase(phrase)
        if idx is None:
            return

        actions.edit.select_all()
        actions.key("left")
        for _ in range(idx):
            actions.key("right")

        for _ in range(len(" ".join(phrase))):
            actions.edit.extend_right()

        return idx

    def samwho_select_xy(start: list[str], end: list[str]):
        """Select from start to end"""
        start_idx = actions.user.samwho_find_phrase(start)
        if start_idx is None:
            return

        end_idx = actions.user.samwho_find_phrase(end)
        if end_idx is None:
            return

        end_idx += len(" ".join(end))

        actions.edit.select_all()
        actions.key("left")
        for _ in range(start_idx):
            actions.key("right")

        for _ in range(end_idx - start_idx):
            actions.edit.extend_right()

    def samwho_find_phrase(phrase: list[str]) -> int | None:
        """Find a word"""
        actions.edit.select_all()
        text = actions.edit.selected_text()
        actions.edit.select_none()

        idx = text.lower().find(" ".join(phrase).lower())
        if idx == -1:
            return None
        return idx

    def samwho_wake():
        """Wake Talon"""
        actions.user.samwho_pop_zoom_on()
        actions.speech.enable()

    def samwho_sleep():
        """Sleep Talon"""
        actions.user.samwho_pop_zoom_off()
        actions.speech.disable()

    def samwho_pop_zoom_off():
        """Turn off pop zoom"""
        actions.tracking.control_zoom_toggle(False)

    def samwho_pop_zoom_on():
        """Turn on pop zoom"""
        actions.tracking.control_zoom_toggle(True)

    def samwho_wake_toggle(show_message: bool = False):
        """Toggle Talon wake/sleep, optionally showing a message."""
        if actions.speech.enabled():
            actions.user.samwho_sleep()
            state = "sleep"
        else:
            actions.user.samwho_wake()
            state = "wake"

        if show_message:
            actions.user.samwho_flash_text(f"talon {state}")

    def samwho_mouse_hiss_set_up():
        """Set mouse hiss scroll direction to up."""
        global _hiss_scroll_up
        _hiss_scroll_up = True
        actions.user.hiss_scroll_up()
        actions.user.samwho_flash_text("mouse hiss up")

    def samwho_mouse_hiss_set_down():
        """Set mouse hiss scroll direction to down."""
        global _hiss_scroll_up
        _hiss_scroll_up = False
        actions.user.hiss_scroll_down()
        actions.user.samwho_flash_text("mouse hiss down")

    def samwho_mouse_hiss_toggle():
        """Toggle mouse hiss scroll direction."""
        if _hiss_scroll_up:
            actions.user.samwho_mouse_hiss_set_down()
        else:
            actions.user.samwho_mouse_hiss_set_up()

    def samwho_track():
        """Toggle mouse tracking"""
        if actions.tracking.control_enabled():
            actions.user.samwho_track_off()
        else:
            actions.user.samwho_track_on()

    def samwho_screenshot_start():
        """Start a screenshot"""
        actions.sleep(0.1)
        actions.key("f13")
        actions.sleep(0.1)
        actions.user.mouse_drag(0)
        actions.user.samwho_track_on()

    def samwho_screenshot_end():
        """End a screenshot"""
        actions.user.mouse_drag_end()
        actions.user.samwho_track_off()

    def samwho_track_on():
        """Turn on mouse tracking"""
        if actions.tracking.control_enabled():
            return
        actions.tracking.control_toggle(True)
        actions.tracking.control_zoom_toggle(False)
        actions.tracking.control_gaze_toggle(True)
        actions.tracking.control_head_toggle(True)

    def samwho_track_off():
        """Turn off mouse tracking"""
        if not actions.tracking.control_enabled():
            return
        actions.tracking.control_toggle(False)
        actions.tracking.control_zoom_toggle(True)
        actions.tracking.control_gaze_toggle(False)
        actions.tracking.control_head_toggle(False)

    def samwho_mute_mic():
        """Mute microphone"""
        actions.sound.set_microphone("None")

    def samwho_unmute_mic():
        """Unmute microphone"""
        actions.sound.set_microphone("Scarlett Solo USB")

    def samwho_start_voicenote():
        """Start voicenote"""
        actions.sleep(0.1)
        actions.user.samwho_pop_zoom_off()
        actions.mode.enable("user.samwho_voicenote")
        actions.mode.disable("command")
        actions.key("alt-n")
        noise.register("pop", _samwho_stop_voicenote)

    def samwho_start_dictation():
        """Start dictation"""
        actions.sleep(0.1)
        actions.user.samwho_pop_zoom_off()
        actions.mode.enable("user.samwho_whisper")
        actions.mode.disable("command")
        actions.key("ctrl-shift-o")
        noise.register("pop", _samwho_stop_dictation)

    def samwho_talon_restart():
        """Restart talon"""
        print("Restarting Talon...")
        os.system("~/bin/restart-talon > /tmp/talon-restart-status.txt 2>&1")


def _samwho_stop_dictation(_active):
    """Stop dictation"""
    actions.sleep(0.1)
    actions.key("ctrl-shift-o")
    actions.mode.disable("user.samwho_whisper")
    actions.mode.enable("command")
    actions.user.samwho_pop_zoom_on()
    noise.unregister("pop", _samwho_stop_dictation)


def _samwho_stop_voicenote(_active):
    """Stop voicenote"""
    actions.sleep(0.1)
    actions.key("alt-s")
    actions.mode.disable("user.samwho_voicenote")
    actions.mode.enable("command")
    actions.user.samwho_pop_zoom_on()
    noise.unregister("pop", _samwho_stop_voicenote)
