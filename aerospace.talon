# AeroSpace is a global menu-bar application, so match it when it is running
# rather than trying to match it as the focused application. These commands
# mirror the bindings in ~/.config/aerospace/aerospace.toml.
user.running: aerospace
os: mac
-

# Use Community's object-first window and workspace vocabulary. These commands
# are intentionally available across focused applications while AeroSpace runs.

window focus left: key(alt-h)
window focus down: key(alt-j)
window focus up: key(alt-k)
window focus right: key(alt-l)

window move left: key(alt-shift-h)
window move down: key(alt-shift-j)
window move up: key(alt-shift-k)
window move right: key(alt-shift-l)

window layout tiles: key(alt-t)
window layout accordion: key(alt-m)
window float: key(alt-f)
window shrink: key(alt-minus)
window grow: key("alt-=")

# AeroSpace workspaces are explicitly numbered 1 through 9 in the config.
workspace one: key(alt-1)
workspace two: key(alt-2)
workspace three: key(alt-3)
workspace four: key(alt-4)
workspace five: key(alt-5)
workspace six: key(alt-6)
workspace seven: key(alt-7)
workspace eight: key(alt-8)
workspace nine: key(alt-9)

window move one: key(alt-shift-1)
window move two: key(alt-shift-2)
window move three: key(alt-shift-3)
window move four: key(alt-shift-4)
window move five: key(alt-shift-5)
window move six: key(alt-shift-6)
window move seven: key(alt-shift-7)
window move eight: key(alt-shift-8)
window move nine: key(alt-shift-9)

workspace back and forth: key(alt-tab)
workspace move monitor next: key(alt-shift-tab)
aero config reload: key(alt-r)
