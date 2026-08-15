app: samwho_ghostty
user.ghostty_focused_program: /^pi$/i
-

# Pi's editor follows readline-like key semantics. Keep Community's
# readline edit contracts active without activating shell command grammar.
tag(): user.readline
# Do not activate terminal or generic_unix_shell here: Pi is a TUI, not a
# shell prompt, so those commands would insert shell text into Pi's editor.

# Operate the surrounding Ghostty/Zellij tabs while Pi is focused.
tag(): user.tabs

# Application controls.
interrupt: key(escape)
prompt clear: key(ctrl-c)
session quit: key(ctrl-d)
suspend: key(ctrl-z)
external editor: key(ctrl-g)
paste clipboard: key(ctrl-v)

# Prompt editing.
cursor up: key(up)
cursor down: key(down)
cursor left: key(left)
cursor right: key(right)
cursor word left: key(alt-left)
cursor word right: key(alt-right)
cursor line start: key(ctrl-a)
cursor line end: key(ctrl-e)
cursor page up: key(pageup)
cursor page down: key(pagedown)
delete backward: key(backspace)
delete forward: key(delete)
delete word backward: key(ctrl-w)
delete word forward: key(alt-d)
prompt undo: key(ctrl--)
prompt new line: key(shift-enter)
prompt submit: key(enter)
prompt autocomplete: key(tab)

# Model and thinking controls. The Ctrl-P and Shift-Tab bindings are safe in
# Zellij; Ctrl-L and Ctrl-T are reserved by this user's Zellij keymap and are
# provided in pi_native.talon instead.
model next: key(ctrl-p)
model previous: key(ctrl-shift-p)
thinking cycle: key(shift-tab)

# Message and tool controls. Ctrl-X is reserved by Zellij's quit binding, so
# Pi's message-copy binding is provided only for native Ghostty in
# pi_native.talon.
tools toggle: key(ctrl-o)
follow up queue: key(alt-enter)
queued message restore: key(alt-up)

# Fullscreen transcript controls.
transcript previous prompt: key(ctrl-shift-up)
transcript next prompt: key(ctrl-shift-down)
transcript search: key(ctrl-shift-f)

# Selector and tree navigation.
selector up: key(up)
selector down: key(down)
selector page up: key(pageup)
selector page down: key(pagedown)
selector confirm: key(enter)
selector cancel: key(escape)
tree fold: key(ctrl-left)
tree unfold: key(ctrl-right)
tree edit label: key(shift-l)
tree toggle labels: key(shift-t)
