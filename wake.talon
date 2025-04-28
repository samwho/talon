mode: command
mode: dictation
mode: sleep
not speech.engine: dragon
-

^talon wake [<phrase>]$: 
    speech.enable()
    tracking.control_zoom_toggle(true)