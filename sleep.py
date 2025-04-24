from talon import actions, app


def disable():
    actions.speech.disable()


app.register("ready", disable)
