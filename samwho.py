import os

from talon import Module, actions

mod = Module()


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
