app: samwho_terminal
user.terminal_focused_program: /^pi$/i
-

# Reuse Community's generic "hunt this/next/previous" search vocabulary.
# pi_talon.py maps those edit actions to fullscreen transcript search.
tag(): user.find

# Application controls.
# Cancel generation, dismiss a dialog, or abort the current operation.
abort: key(escape)
# Clear a nonempty prompt; Pi exits if Ctrl-C is pressed again on an empty prompt.
clear prompt: key(ctrl-c)
# Exit Pi when the prompt is empty.
quit: key(ctrl-d)
# Suspend Pi to the background on Unix.
suspend: key(ctrl-z)
# Open the current prompt in Pi's configured external editor.
external editor: key(ctrl-g)
# Paste an image or text from the system clipboard.
paste image: key(ctrl-v)

# Prompt editor navigation.
# Move the prompt cursor, or browse history at a prompt boundary.
up: key(up)
down: key(down)
# Move the prompt cursor by one character.
left: key(left)
right: key(right)
# Move the prompt cursor by one word.
word left: key(alt-left)
word right: key(alt-right)
# Move to the start or end of the current prompt line.
line start: key(ctrl-a)
line end: key(ctrl-e)
# Ask Pi for a character, then jump to its next or previous occurrence.
jump forward: key(ctrl-])
jump backward: key(ctrl-alt-])
# Move the prompt editor by a page without scrolling the fullscreen transcript.
editor up: key(ctrl-pageup)
editor down: key(ctrl-pagedown)

# Prompt editor deletion and kill ring.
# Delete one character before or after the cursor.
backspace: key(backspace)
delete: key(delete)
# Delete the word before the cursor. Community's "delete word" command is
# supplied by user.readline and handles the word after the cursor.
erase word: key(ctrl-w)
# Delete from the cursor to the start of the line.
erase start: key(ctrl-u)
# Restore the most recently killed text, then cycle older killed text.
yank: key(ctrl-y)
yank next: key(alt-y)
# Undo the last prompt edit.
undo: key(ctrl--)
# Insert a newline without submitting the prompt.
new line: key(shift-enter)
# Submit the current prompt.
submit: key(enter)
# Complete the current slash command or selectable value.
complete: key(tab)

# Models, thinking, tools, and queued messages. Bindings intercepted by some
# multiplexers are supplied by their more-specific Pi context files.
# Select the previous configured model.
model previous: key(ctrl-shift-p)
# Cycle through the model's supported thinking levels.
thinking cycle: key(shift-tab)
# Collapse or expand tool-call output.
tools toggle: key(ctrl-o)
# Queue the current prompt as a follow-up while Pi is working.
queue: key(alt-enter)
# Restore queued follow-ups to the prompt editor.
dequeue: key(alt-up)

# Fullscreen transcript. Community's global edit vocabulary also works here:
# "go top/bottom", "go page up/down", and "scroll up/down" call the Pi-specific
# edit implementations in pi_talon.py.
# Scroll the fullscreen transcript by one page.
page up: key(pageup)
page down: key(pagedown)
# Jump between marked user prompts in the transcript.
prompt previous: key(ctrl-shift-up)
prompt next: key(ctrl-shift-down)
# Open transcript search. "hunt this" provides the Community equivalent.
transcript search: key(ctrl-shift-f)
# Move between transcript-search matches.
search next: key(enter)
search previous: key(ctrl-shift-g)
# Close transcript search.
search close: key(escape)
# Jump to the beginning or end of the transcript.
transcript top: key(home)
transcript bottom: key(end)

# Selectors and session tree.
# Move through the current selector.
select up: key(up)
select down: key(down)
# Confirm or cancel the current selector.
select confirm: key(enter)
select cancel: key(escape)
# Fold or unfold the selected session-tree branch.
tree fold: key(ctrl-left)
tree unfold: key(ctrl-right)
# Edit the selected tree node's label.
label edit: key(shift-l)
# Show or hide timestamps on tree labels.
timestamps: key(shift-t)
# Choose the default, user-only, or all-entry tree filter.
filter default: key(ctrl-d)
filter user: key(ctrl-u)
filter all: key(ctrl-a)
# Cycle forward or backward through tree filters.
filter next: key(ctrl-o)
filter previous: key(ctrl-shift-o)
