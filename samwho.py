import os

from talon import Module

mod = Module()


@mod.action_class
class Actions:
    def open_obsidian_daily_note():
        """My custom date function"""
        return os.system(
            'open "obsidian://advanced-uri?vault=Universe&daily=true&mode=append"'
        )
