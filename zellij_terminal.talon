app: samwho_terminal
user.terminal_is_zellij: true
user.zellij_program: /^(bash|zsh|fish|sh|dash|ksh|tcsh|csh|nu|nushell|pwsh|powershell)$/i
-

# Community's generic terminal and shell contracts inside Zellij.
tag(): terminal
tag(): user.generic_unix_shell
tag(): user.readline
tag(): user.git
tag(): user.file_manager
tag(): user.unix_utilities
