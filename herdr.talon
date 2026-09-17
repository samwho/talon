app: samwho_terminal
user.terminal_is_herdr: true
-

# Shared Community capabilities that Herdr implements through its CLI.
# user.tabs supplies tab new/previous/next/close/reopen, go tab <number>,
# go tab final, and tab duplicate. Reopen reports unsupported because the CLI
# has no reopen operation.
tag(): user.tabs
# user.splits supplies split creation, zoom, close, navigation, and reset
# vocabulary. Unsupported orientation/equalize/index operations report errors.
tag(): user.splits

# Workspaces.
# Create and focus a workspace rooted at the focused pane's working directory.
workspace new: user.samwho_herdr_workspace_new()
# Cycle through workspaces, wrapping at either end.
workspace previous: user.samwho_herdr_workspace_previous()
workspace next: user.samwho_herdr_workspace_next()
# Focus a workspace by the number displayed in Herdr.
go workspace <number>: user.samwho_herdr_workspace_jump(number)
# Rename the focused workspace using the rest of the utterance.
workspace rename <user.text>$: user.samwho_herdr_workspace_rename(text)
# Close the focused workspace. Herdr still enforces worktree-group safeguards.
workspace close: user.samwho_herdr_workspace_close()

# Tabs beyond Community's shared tab vocabulary.
# Rename the focused tab using the rest of the utterance.
tab rename <user.text>$: user.samwho_herdr_tab_rename(text)

# Pane focus, arrangement, and sizing.
# Focus the nearest pane in the named direction.
pane focus {user.arrow_key}: user.samwho_herdr_pane_focus(arrow_key)
# Swap the focused pane with its neighbor in the named direction.
pane swap {user.arrow_key}: user.samwho_herdr_pane_swap(arrow_key)
# Move a split boundary in the named direction by ten percent, or by an
# explicitly spoken percentage.
pane resize {user.arrow_key} [<number>]:
    amount = number or 10
    user.samwho_herdr_pane_resize(arrow_key, amount)
# Rename the focused pane using the rest of the utterance, or clear its name.
pane rename <user.text>$: user.samwho_herdr_pane_rename(text)
pane name clear: user.samwho_herdr_pane_name_clear()
# Move the focused pane into a newly created tab or workspace.
pane new tab: user.samwho_herdr_pane_to_tab()
pane new workspace: user.samwho_herdr_pane_to_workspace()

# Recognized coding agents.
# Focus the next unread agent. Herdr exposes unseen completions through the
# CLI as `agent_status: done`; focusing that agent marks it seen.
(goneck | gonext): user.samwho_herdr_unread_next()
# Cycle through all agents known to the local Herdr server.
agent previous: user.samwho_herdr_agent_previous()
agent next: user.samwho_herdr_agent_next()
# Focus an agent by its one-based order in `herdr agent list`.
go agent <number>: user.samwho_herdr_agent_jump(number)
# Assign a lowercase snake-case name to the focused agent.
agent rename <user.text>$:
    name = user.formatted_text(text, "SNAKE_CASE")
    user.samwho_herdr_agent_rename(name)
# Remove the focused agent's custom name.
agent name clear: user.samwho_herdr_agent_name_clear()

# Git worktree-backed workspaces.
# Create and focus a worktree for a new dash-separated branch name.
worktree new <user.text>$:
    branch = user.formatted_text(text, "DASH_SEPARATED")
    user.samwho_herdr_worktree_create(branch)
# Open and focus the existing worktree path currently on the clipboard.
worktree open: user.samwho_herdr_worktree_open(clip.text())
# Remove the focused worktree without forcing or bypassing repository trust.
worktree remove: user.samwho_herdr_worktree_remove()
