correct <phrase> (to|two|too) <phrase>:
    user.selectXY(phrase_1, phrase_2)

correct <phrase>:
    user.correct(phrase)

obsidian today:
    user.open_obsidian_daily_note()

seek <phrase>:
  user.superkey(phrase)

whisper:
  key("alt-y")
  speech.disable()

sleep:
  speech.disable()

down:
  user.mouse_scroll_up(10)

up:
  user.mouse_scroll_down(10)
