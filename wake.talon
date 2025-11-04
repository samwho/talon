mode: command
mode: dictation
mode: sleep
os: mac
not speech.engine: dragon
not tag: user.deep_sleep
-

^talon wake [<phrase>]$:
    user.wake()
