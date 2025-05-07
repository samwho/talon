settings():
    speech.timeout = 0.5

    user.mouse_enable_hiss_scroll = true
    user.hiss_scroll_debounce_time = 250
    user.mouse_continuous_scroll_amount = -25
    user.mouse_hide_mouse_gui = true
    user.context_sensitive_dictation = true

    tracking.zoom_height = 150
    tracking.zoom_width = 200
    tracking.zoom_scale = 6


correct <phrase> (to|two|too) <phrase>:
    user.selectXY(phrase_1, phrase_2)

correct <phrase>:
    user.correct(phrase)

obsidian today:
    user.open_obsidian_daily_note()

scroll down:
  edit.down()
  repeat(10)

scroll up:
  edit.up()
  repeat(10)

track:
  user.track()

^talon sleep$:
  user.sleep()

^copy permalink$:
  user.vscode("issue.copyGithubPermalink")