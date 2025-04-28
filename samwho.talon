settings():
    user.mouse_enable_hiss_scroll = true
    user.hiss_scroll_debounce_time = 200
    user.mouse_continuous_scroll_amount = -15
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

seek <phrase>:
  user.superkey(phrase)

click:
  key("cmd-ctrl-alt-b")

whisper:
  key("alt-y")
  speech.disable()

chat gpt | chat:
  key("alt-space")

deck(pedal_right:down):
  key(alt-y:down)

deck(pedal_right:up):
  key(alt-y:up)

deck(pedal_left:down):
  speech.enable()

deck(pedal_left:up):
  speech.disable()

deck(pedal_middle):
  key("enter")

scroll down:
  edit.down()
  repeat(10)

scroll up:
  edit.up()
  repeat(10)

track:
  tracking.control_toggle()

^talon sleep$:
  speech.disable()
  tracking.control_zoom_toggle(false)