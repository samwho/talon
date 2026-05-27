# Agent Notes

This repository is a personal Talon Voice configuration. Talon loads `.talon`
files as voice command grammars and companion `.py` files as Python modules that
define custom actions, settings, callbacks, and app-specific behavior.

## Useful References

- Official Talon docs: https://talonvoice.com/docs/
- Community wiki: https://talon.wiki/
- Talon app bundle stubs on this machine:
  `/Applications/Talon.app/Contents/Resources/python/lib/python3.13/site-packages/talon`

The app bundle contains `.pyi` files for Talon's API. These are useful for
understanding signatures, but some runtime behavior is dynamic and intentionally
does not look like normal Python to static type checkers.

## Project Shape

- `*.talon` files define spoken commands, contexts, tags, modes, settings, and
  calls into Talon actions.
- `*.py` files define custom actions and support functions.
- App-specific files usually match the target app name, such as `zed.talon`,
  `mail.talon`/`mail.py`, `zen.talon`, and `beeper/`.
- `samwho.py` and `samwho.talon` contain general-purpose personal commands,
  wake/sleep behavior, mouse tracking toggles, correction helpers, and Obsidian
  integration.
- `flash_text.py` implements a custom on-screen flash text action used for
  status messages.

## Talon Patterns

- Import Talon APIs with `from talon import ...`; these imports resolve inside
  Talon's embedded runtime, not from normal PyPI dependencies.
- Use `Module()` for defining reusable user actions, settings, modes, and tags.
- Use `Context()` for app/platform-specific action implementations.
- Talon action classes are decorated with `@mod.action_class` or
  `@ctx.action_class(...)`. Methods inside these classes intentionally omit
  `self`; Talon registers them as actions rather than ordinary instance methods.
- `.talon` command files call Python actions with `user.action_name(...)`.
- It is normal for Talon APIs such as `actions.user`, `settings.get`, and app UI
  objects to be dynamically typed or broad in the bundled stubs.

## Editing Guidance

- Keep changes small and local to the app or feature being touched.
- Do not convert this repo into a normal Python package or add runtime package
  metadata just to satisfy editors; Talon owns the runtime environment.
- Prefer following existing command names and keybinding style in nearby
  `.talon` files.
- When adding a new custom action, define it in Python under a Talon action
  class, then call it from the relevant `.talon` file.
- When a command sends a key chord to an app, make sure the app itself has a
  matching binding if needed. Talon only sends the keystroke.
- Be careful with dirty worktrees. This is a personal config repo and unrelated
  local changes are common.

## Validation

- For Python syntax checks, use the local editor-only venv if present:
  `.zed/.venv/bin/python -m py_compile <file.py>`.
- Talon behavior is ultimately validated by Talon loading the files and the
  relevant voice command working in the target app.
- Static Python diagnostics can be noisy because Talon uses dynamic decorators
  and runtime-provided APIs. Do not "fix" Talon action methods by adding `self`.
