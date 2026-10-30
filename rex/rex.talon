app: samwho_rex
-

# Shared vocabulary is implemented through named Rex actions in rex_talon.py.
tag(): user.tabs
tag(): user.splits
tag(): user.command_search
tag(): user.find

# Cycle through other terminal blocks reporting done or blocked.
(goneck | gonext): user.samwho_rex_waiting_next()

