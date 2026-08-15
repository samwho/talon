app: samwho_ghostty
-

# Shared Community contracts. Their app-specific actions are implemented in
# ghostty.py, so the common vocabulary works without an app prefix.
tag(): user.tabs
tag(): user.splits
tag(): user.command_search

# Windows and app-specific tab controls. The Community window grammar supplies
# window new/close/next/last/hide; these are Ghostty-specific additions.
window previous: user.samwho_ghostty_action("goto_window:previous")
window close all: user.samwho_ghostty_action("close_all_windows")
window float: user.samwho_ghostty_action("toggle_window_float_on_top")

tab <number>: user.samwho_ghostty_goto_tab(number)
tab final: user.samwho_ghostty_action("last_tab")
tab move left: user.samwho_ghostty_action("move_tab:-1")
tab move right: user.samwho_ghostty_action("move_tab:1")
tab rename: user.samwho_ghostty_action("prompt_tab_title")

surface close: user.samwho_ghostty_action("close_surface")
surface title: user.samwho_ghostty_action("prompt_surface_title")

# The shared splits vocabulary covers the common operations. These aliases
# retain Ghostty's more explicit create/focus/resize controls.
split new right: user.samwho_ghostty_action("new_split:right")
split new left: user.samwho_ghostty_action("new_split:left")
split new down: user.samwho_ghostty_action("new_split:down")
split new up: user.samwho_ghostty_action("new_split:up")
split focus previous: user.samwho_ghostty_action("goto_split:previous")
split focus next: user.samwho_ghostty_action("goto_split:next")
split focus up: user.samwho_ghostty_action("goto_split:up")
split focus down: user.samwho_ghostty_action("goto_split:down")
split focus left: user.samwho_ghostty_action("goto_split:left")
split focus right: user.samwho_ghostty_action("goto_split:right")
split resize up: user.samwho_ghostty_action("resize_split:up,10")
split resize down: user.samwho_ghostty_action("resize_split:down,10")
split resize left: user.samwho_ghostty_action("resize_split:left,10")
split resize right: user.samwho_ghostty_action("resize_split:right,10")
split equalize: user.samwho_ghostty_action("equalize_splits")
split zoom: user.samwho_ghostty_action("toggle_split_zoom")

# Scrollback, search, and selection
scroll top: user.samwho_ghostty_action("scroll_to_top")
scroll bottom: user.samwho_ghostty_action("scroll_to_bottom")
scroll page up: user.samwho_ghostty_action("scroll_page_up")
scroll page down: user.samwho_ghostty_action("scroll_page_down")
scroll selection: user.samwho_ghostty_action("scroll_to_selection")
prompt previous: user.samwho_ghostty_action("jump_to_prompt:-1")
prompt next: user.samwho_ghostty_action("jump_to_prompt:1")

search: user.samwho_ghostty_action("start_search")
search selection: user.samwho_ghostty_action("search_selection")
search next: user.samwho_ghostty_action("navigate_search:next")
search previous: user.samwho_ghostty_action("navigate_search:previous")
search close: user.samwho_ghostty_action("end_search")

selection left: user.samwho_ghostty_action("adjust_selection:left")
selection right: user.samwho_ghostty_action("adjust_selection:right")
selection up: user.samwho_ghostty_action("adjust_selection:up")
selection down: user.samwho_ghostty_action("adjust_selection:down")
selection page up: user.samwho_ghostty_action("adjust_selection:page_up")
selection page down: user.samwho_ghostty_action("adjust_selection:page_down")
selection home: user.samwho_ghostty_action("adjust_selection:home")
selection end: user.samwho_ghostty_action("adjust_selection:end")

# Clipboard and screen files
copy: user.samwho_ghostty_action("copy_to_clipboard:mixed")
paste: user.samwho_ghostty_action("paste_from_clipboard")
paste selection: user.samwho_ghostty_action("paste_from_selection")
copy URL: user.samwho_ghostty_action("copy_url_to_clipboard")
copy title: user.samwho_ghostty_action("copy_title_to_clipboard")
select all: user.samwho_ghostty_action("select_all")
screen file copy: user.samwho_ghostty_action("write_screen_file:copy,plain")
screen file paste: user.samwho_ghostty_action("write_screen_file:paste,plain")
screen file open: user.samwho_ghostty_action("write_screen_file:open,plain")

# Font and terminal state
font increase: user.samwho_ghostty_action("increase_font_size:1")
font decrease: user.samwho_ghostty_action("decrease_font_size:1")
font reset: user.samwho_ghostty_action("reset_font_size")
clear: user.samwho_ghostty_action("clear_screen")
reset terminal: user.samwho_ghostty_action("reset")
undo: user.samwho_ghostty_action("undo")
redo: user.samwho_ghostty_action("redo")
fullscreen: user.samwho_ghostty_action("toggle_fullscreen")
readonly: user.samwho_ghostty_action("toggle_readonly")
mouse reporting: user.samwho_ghostty_action("toggle_mouse_reporting")
secure input: user.samwho_ghostty_action("toggle_secure_input")
background opacity: user.samwho_ghostty_action("toggle_background_opacity")
visible: user.samwho_ghostty_action("toggle_visibility")
quick terminal: user.samwho_ghostty_action("toggle_quick_terminal")

# Ghostty controls
config: user.samwho_ghostty_action("open_config")
reload: user.samwho_ghostty_action("reload_config")
command palette: user.samwho_ghostty_action("toggle_command_palette")
inspector: user.samwho_ghostty_action("inspector:toggle")
check updates: user.samwho_ghostty_action("check_for_updates")
quit: user.samwho_ghostty_action("quit")
