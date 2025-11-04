app: vscode
-

wax | whacks:
	user.vscode('editor.action.smartSelect.expand')

wane:
	user.vscode('editor.action.smartSelect.shrink')

tab hunt:
	key("cmd-p")
	sleep(50ms)
	insert("edt ")

^toggle mark$:
  user.vscode("bookmarks.toggle")

^toggle mark <user.text>$:
  user.vscode("bookmarks.toggleLabeled")
  sleep(50ms)
  insert(text)
  key(enter)

go mark <user.text>:
  user.vscode("bookmarks.listFromAllFiles")
  sleep(50ms)
  insert(text)
  key(enter)

delete all marks:
  user.vscode("bookmarks.clearFromAllFiles")

(split | tab) shrink:
  user.vscode("workbench.action.decreaseViewWidth")

(split | tab) grow:
  user.vscode("workbench.action.increaseViewWidth")


tab merge left:
  user.vscode("workbench.action.moveEditorToLeftGroup")

tab merge right:
  user.vscode("workbench.action.moveEditorToRightGroup")

tab merge up:
  user.vscode("workbench.action.moveEditorToAboveGroup")

tab merge down:
  user.vscode("workbench.action.moveEditorToBelowGroup")

terminal new:
  user.vscode("workbench.action.createTerminalEditorSide")
  user.vscode("workbench.action.moveEditorToLeftGroup")

pane up:
  user.vscode("workbench.action.focusAboveGroup")

pane down:
  user.vscode("workbench.action.focusBelowGroup")

pane left:
  user.vscode("workbench.action.focusLeftGroup")

pane right:
  user.vscode("workbench.action.focusRightGroup")