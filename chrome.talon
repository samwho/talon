app: chrome
-

tab close others:
  # Chrome has no native shortcut for this; use the Tab menu.
  key(ctrl-f2)
  sleep(50ms)
  insert("tab")
  key(down)
  sleep(50ms)
  key(down)
  key(down)
  key(down)
  key(down)
  key(down)
  key(down)
  key(down)
  key(enter)
