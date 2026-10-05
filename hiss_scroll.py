"""Use Community's scroll engine for hiss without changing the speech grammar."""

import sys

from talon import Context, actions, settings

ctx = Context()
ctx.matches = "os: mac"


@ctx.action_class("user")
class HissScrollActions:
    def noise_trigger_hiss(active: bool):
        # Resolve at action time: Community may load or reload after this file.
        # Its public start actions also enable user.continuous_scrolling, so
        # reuse the scroll state directly instead. This depends on Community's
        # plugin/mouse/mouse_scroll.py internals, without modifying that module.
        mouse_scroll = sys.modules["user.community.plugin.mouse.mouse_scroll"]
        state = mouse_scroll.scrolling_state

        if not active:
            if mouse_scroll.ctx.tags:
                actions.user.mouse_scroll_stop()
            else:
                # Don't assign even an empty tag list for ordinary hiss release.
                state.stop_scrolling_job()
            return

        if not settings.get("user.mouse_enable_hiss_scroll"):
            return

        if mouse_scroll.ctx.tags:
            # Hand over from voice/gaze scrolling, clearing its tag and GUI.
            actions.user.mouse_scroll_stop()

        direction = (
            mouse_scroll.ScrollingDirection.UP
            if mouse_scroll.hiss_scroll_up
            else mouse_scroll.ScrollingDirection.DOWN
        )
        state.scroller.set_direction(direction)
        actions.user.mouse_scroll_set_speed(None)
        state.start_continuous_scrolling_job()
