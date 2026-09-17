settings():
    speech.timeout = 0.5

    user.mouse_enable_hiss_scroll = true
    user.hiss_scroll_debounce_time = 250
    user.mouse_continuous_scroll_amount = -10
    user.mouse_continuous_scroll_acceleration = 3
    user.mouse_hide_mouse_gui = true

    tracking.zoom_height = 150
    tracking.zoom_width = 200
    tracking.zoom_scale = 6


correct <phrase> (to|two|too) <phrase>:
    user.samwho_select_xy(phrase_1, phrase_2)

correct <phrase>:
    user.samwho_correct(phrase)

scroll down:
  edit.down()
  repeat(10)

scroll up:
  edit.up()
  repeat(10)

track:
  user.samwho_track()

[left] (triple | trip) (touch | click) <user.timestamped_prose>:
  user.click_text(timestamped_prose)
  user.click_text(timestamped_prose)
  user.click_text(timestamped_prose)

key(alt-y):
  user.samwho_start_dictation()

key(alt-ctrl-cmd-shift-a):
  user.samwho_wake_toggle(true)

key(alt-ctrl-cmd-shift-b):
  user.samwho_mouse_hiss_toggle()

^talon restart$:
  user.samwho_talon_restart()

^whisper$:
  user.samwho_start_dictation()

^(code|term)$:
  user.switcher_focus("Ghostty")

^(browse|browser|brace)$:
  user.switcher_focus("Google Chrome")

^slack$:
  user.switcher_focus("Slack")
