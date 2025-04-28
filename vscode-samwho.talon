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

split shrink:
  user.vscode("workbench.action.decreaseEditorWidth")

split grow:
  user.vscode("workbench.action.increaseEditorWidth")