app: samwho_ghostty
user.terminal_focused_program: /^pi$/i
user.terminal_is_herdr: false
-

# Native Ghostty passes Pi's readline-style editing shortcuts through directly.
tag(): user.readline

# Delete from the cursor to the end of the current prompt line.
erase end: key(ctrl-k)

# Pi bindings that Herdr intercepts but native Ghostty passes through.
# Open the model selector.
model select: key(ctrl-l)
# Cycle to the next configured model.
model next: key(ctrl-p)
# Collapse or expand model-thinking blocks.
thinking toggle: key(ctrl-t)
# Copy the last assistant message, or the selected tree message.
message copy: key(ctrl-x)
# Show or hide tool results in the session tree.
filter tools: key(ctrl-t)
# Show only labeled entries in the session tree.
filter labels: key(ctrl-l)
